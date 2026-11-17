# Copyright (c) 2026, Nguyen Long Vu and Contributors
# See license.txt

from frappe.tests.utils import FrappeTestCase

from order_management.order_management.exceptions import OrderRuleError
from order_management.tests.factories import make_item


class TestOrderItem(FrappeTestCase):
	def test_default_rate_must_be_positive(self):
		for rate in (0, -1):
			with self.subTest(rate=rate), self.assertRaises(OrderRuleError):
				make_item(default_rate=rate)
