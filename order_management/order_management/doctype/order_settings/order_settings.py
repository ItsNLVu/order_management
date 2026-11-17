# Copyright (c) 2026, Nguyen Long Vu and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from order_management.order_management.services import validators


class OrderSettings(Document):
	def validate(self):
		validators.ensure_positive(self, "report_default_days")
