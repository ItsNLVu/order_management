from datetime import date, datetime

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import formatdate

from order_management.order_management.constants import OrderAction
from order_management.order_management.report.daily_revenue.daily_revenue import execute
from order_management.tests.factories import act, backdate, make_order, override_settings

DAY_1 = date(2020, 1, 1)
DAY_2 = date(2020, 1, 2)


def order_created_at(created, action=None, qty=1, rate=100_000):
	order = make_order(qty=qty, rate=rate)
	if action:
		act(order, action, reason="test")
	backdate(order.name, created)
	return order


def rows(from_date, to_date):
	return execute({"from_date": from_date, "to_date": to_date})[1]


class TestDailyRevenue(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# Day 1: two delivered, the second at 23:59:59
		order_created_at(datetime(2020, 1, 1, 8, 0), OrderAction.DELIVER, qty=2)
		order_created_at(datetime(2020, 1, 1, 23, 59, 59), OrderAction.DELIVER, qty=1)
		# Day 2: one delivered at 00:00, one cancelled, one new
		order_created_at(datetime(2020, 1, 2, 0, 0, 0), OrderAction.DELIVER, qty=5)
		order_created_at(datetime(2020, 1, 2, 9, 0), OrderAction.CANCEL)
		order_created_at(datetime(2020, 1, 2, 10, 0))
		# Day 3 is empty
		order_created_at(datetime(2020, 1, 4, 12, 0), OrderAction.DELIVER, qty=1)

	def test_groups_delivered_orders_by_creation_date(self):
		result = rows(DAY_1, date(2020, 1, 4))
		self.assertEqual(
			[(r.order_date, r.order_count, r.total_amount) for r in result],
			[(DAY_1, 2, 300_000), (DAY_2, 1, 500_000), (date(2020, 1, 4), 1, 100_000)],
		)

	def test_range_is_inclusive_on_both_ends(self):
		self.assertEqual([r.order_date for r in rows(DAY_2, DAY_2)], [DAY_2])
		self.assertEqual([r.order_date for r in rows(DAY_1, DAY_1)], [DAY_1])

	def test_empty_range_explains_why(self):
		_columns, data, message, chart = execute({"from_date": "2020-01-03", "to_date": "2020-01-03"})
		self.assertEqual(data, [])
		self.assertIsNone(chart)
		self.assertIn(formatdate("2020-01-03"), message)

	def test_chart_matches_the_table(self):
		_columns, data, message, chart = execute({"from_date": "2020-01-01", "to_date": "2020-01-04"})
		self.assertIsNone(message)
		self.assertEqual(chart["data"]["datasets"][0]["values"], [row.total_amount for row in data])

	def test_from_date_after_to_date_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			rows(DAY_2, DAY_1)

	def test_default_range_comes_from_settings(self):
		from order_management.order_management.report.daily_revenue.daily_revenue import get_date_range

		with override_settings(report_default_days=7):
			from_date, to_date = get_date_range(frappe._dict(to_date="2020-01-10"))
		self.assertEqual((from_date, to_date), (date(2020, 1, 4), date(2020, 1, 10)))
