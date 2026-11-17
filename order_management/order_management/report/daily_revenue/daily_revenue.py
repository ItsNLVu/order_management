# Copyright (c) 2026, Nguyen Long Vu and contributors
# For license information, please see license.txt

"""Daily revenue: one row per creation date with the number and total of delivered orders.

Aggregation runs in SQL. The date filter is a half-open range on `creation`
(from 00:00 up to the day after `to_date`), so the (status, creation) index can be used.
"""

import frappe
from frappe import _
from frappe.query_builder.functions import Count, Date, Sum
from frappe.utils import add_days, formatdate, getdate, today

from order_management.order_management.constants import DocTypes, OrderStatus
from order_management.order_management.services.settings import get_settings
from order_management.order_management.services.status_machine import STATUS_COLORS


def execute(filters=None):
	from_date, to_date = get_date_range(frappe._dict(filters or {}))
	data = get_data(from_date, to_date)
	return get_columns(), data, get_empty_message(data, from_date, to_date), get_chart(data)


def get_date_range(filters):
	to_date = getdate(filters.to_date or today())
	from_date = getdate(filters.from_date or add_days(to_date, 1 - get_settings().report_default_days))
	if from_date > to_date:
		frappe.throw(_("From Date must be on or before To Date."), title=_("Check the Date Range"))
	return from_date, to_date


def get_columns():
	return [
		{"fieldname": "order_date", "label": _("Date"), "fieldtype": "Date", "width": 140},
		{"fieldname": "order_count", "label": _("Delivered Orders"), "fieldtype": "Int", "width": 160},
		{"fieldname": "total_amount", "label": _("Total Amount"), "fieldtype": "Currency", "width": 180},
	]


def get_data(from_date, to_date):
	order = frappe.qb.DocType(DocTypes.ORDER)
	order_date = Date(order.creation)
	return (
		frappe.qb.from_(order)
		.select(
			order_date.as_("order_date"),
			Count(order.name).as_("order_count"),
			Sum(order.amount).as_("total_amount"),
		)
		.where(order.status == OrderStatus.DELIVERED.value)
		.where(order.creation >= from_date)
		.where(order.creation < add_days(to_date, 1))
		.groupby(order_date)
		.orderby(order_date)
	).run(as_dict=True)


def get_empty_message(data, from_date, to_date):
	"""Say why the report is empty and what fills it, instead of a bare 'no data'."""
	if data:
		return None
	return (
		_("No delivered orders were created between {0} and {1}.").format(
			formatdate(from_date), formatdate(to_date)
		)
		+ " "
		+ _("Choose a wider date range, or deliver an order first.")
	)


def get_chart(data):
	"""Bars of the same totals as the table. Green because only Delivered orders count."""
	if not data:
		return None
	return {
		"data": {
			# Day and month only, so labels fit under each bar; the table has the full date
			"labels": [formatdate(row.order_date, "dd-MM") for row in data],
			"datasets": [{"name": _("Total Amount"), "values": [row.total_amount for row in data]}],
		},
		"type": "bar",
		"fieldtype": "Currency",
		"colors": [STATUS_COLORS[OrderStatus.DELIVERED]],
		"barOptions": {"spaceRatio": 0.4},
	}
