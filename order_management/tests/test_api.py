import frappe
from frappe.tests.utils import FrappeTestCase

from order_management.api import apply_action
from order_management.order_management.constants import OrderStatus
from order_management.tests.factories import make_order


class TestApplyAction(FrappeTestCase):
	def test_unknown_action_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			apply_action(make_order().name, "ship")

	def test_returns_the_updated_order(self):
		result = apply_action(make_order().name, "deliver")
		self.assertEqual(result["status"], OrderStatus.DELIVERED.value)

	def test_user_without_access_is_refused(self):
		order = make_order()
		frappe.set_user("Guest")
		try:
			with self.assertRaises(frappe.PermissionError):
				apply_action(order.name, "deliver")
		finally:
			frappe.set_user("Administrator")
