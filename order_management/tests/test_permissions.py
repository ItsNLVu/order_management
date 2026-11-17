import frappe
from frappe.tests.utils import FrappeTestCase

from order_management.order_management.constants import DocTypes, Role
from order_management.tests.factories import as_user, ensure_test_user


class TestPermissions(FrappeTestCase):
	"""Who may do what, checked against the permission engine rather than the form."""

	def assertRights(self, doctype, role, expected):
		user = ensure_test_user(role)
		for right, allowed in expected.items():
			with self.subTest(doctype=doctype, role=role.value, right=right):
				self.assertEqual(bool(frappe.has_permission(doctype, right, user=user)), allowed)

	def test_order_user_reads_masters_but_cannot_change_them(self):
		for doctype in (DocTypes.CUSTOMER, DocTypes.ITEM):
			self.assertRights(
				doctype, Role.ORDER_USER, {"read": True, "create": False, "write": False, "delete": False}
			)

	def test_order_user_cannot_open_settings(self):
		self.assertRights(DocTypes.SETTINGS, Role.ORDER_USER, {"read": False, "write": False})

	def test_order_manager_maintains_masters_and_settings(self):
		for doctype in (DocTypes.CUSTOMER, DocTypes.ITEM):
			self.assertRights(
				doctype, Role.ORDER_MANAGER, {"read": True, "create": True, "write": True, "delete": True}
			)
		self.assertRights(DocTypes.SETTINGS, Role.ORDER_MANAGER, {"read": True, "write": True})

	def test_order_user_cannot_insert_a_customer(self):
		with as_user(Role.ORDER_USER), self.assertRaises(frappe.PermissionError):
			frappe.get_doc({"doctype": DocTypes.CUSTOMER, "customer_name": "Not allowed"}).insert()

	def test_only_managers_run_the_report(self):
		report = frappe.get_doc("Report", "Daily Revenue")
		for role, allowed in ((Role.ORDER_USER, False), (Role.ORDER_MANAGER, True)):
			with self.subTest(role=role.value), as_user(role):
				self.assertEqual(bool(report.is_permitted()), allowed)
