"""Guards for the few places Frappe makes us repeat a value declared in Python."""

import csv
import os

import frappe
from frappe.tests.utils import FrappeTestCase

from order_management.order_management.constants import DocTypes, OrderStatus, Role
from order_management.order_management.services.status_machine import TRANSITIONS


class TestMetadataSync(FrappeTestCase):
	def test_status_options_match_enum(self):
		field = frappe.get_meta(DocTypes.ORDER).get_field("status")
		self.assertEqual(field.options.split("\n"), [s.value for s in OrderStatus])
		self.assertEqual(field.default, OrderStatus.NEW.value)

	def test_transition_fields_exist_and_are_read_only(self):
		order_meta = frappe.get_meta(DocTypes.ORDER)
		settings_meta = frappe.get_meta(DocTypes.SETTINGS)
		for t in TRANSITIONS.values():
			for fieldname in filter(None, (t.at_field, t.by_field, t.reason_field)):
				with self.subTest(field=fieldname):
					self.assertTrue(order_meta.get_field(fieldname).read_only)
			if t.reason_setting:
				self.assertIsNotNone(settings_meta.get_field(t.reason_setting))

	def test_roles_exist(self):
		for role in Role:
			self.assertTrue(frappe.db.exists("Role", role.value))

	def test_vietnamese_translation_covers_statuses_actions_and_roles(self):
		path = os.path.join(frappe.get_app_path("order_management"), "translations", "vi.csv")
		with open(path, encoding="utf-8") as f:
			translated = {row[0] for row in csv.reader(f) if row}
		expected = (
			{s.value for s in OrderStatus} | {t.label for t in TRANSITIONS.values()} | {r.value for r in Role}
		)
		self.assertEqual(expected - translated, set())
