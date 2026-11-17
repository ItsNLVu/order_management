# Copyright (c) 2026, Nguyen Long Vu and contributors
# For license information, please see license.txt

"""Daily revenue: one row per creation date with the number and total of delivered orders.

Aggregation runs in SQL. The date filter is a half-open range on `creation`
(from 00:00 up to the day after `to_date`), so the (status, creation) index can be used.
"""

import frappe
from frappe import _
from frappe.query_builder.functions import Count, Date, Sum
from frappe.utils import add_days, getdate, today

from order_management.order_management.constants import DocTypes, OrderStatus
from order_management.order_management.services.settings import get_settings


def execute(filters=None):
	from_date, to_date = get_date_range(frappe._dict(filters or {}))
	return get_columns(), get_data(from_date, to_date)


def get_date_range(filters):
	to_date = getdate(filters.to_date or today())
	from_date = getdate(filters.from_date or add_days(to_date, 1 - get_settings().report_default_days))
	if from_date > to_date:
		frappe.throw(_("From Date must be on or before To Date."))
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
