# Copyright (c) 2026, Nguyen Long Vu and Contributors
# See license.txt

from frappe.tests.utils import FrappeTestCase

from order_management.order_management.exceptions import OrderRuleError
from order_management.tests.factories import override_settings


class TestOrderSettings(FrappeTestCase):
	def test_report_range_must_be_positive(self):
		with self.assertRaises(OrderRuleError), override_settings(report_default_days=0):
			pass
