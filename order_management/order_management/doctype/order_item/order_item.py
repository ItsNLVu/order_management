# Copyright (c) 2026, Nguyen Long Vu and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from order_management.order_management.services import validators


class OrderItem(Document):
	def validate(self):
		validators.ensure_within_limits(self, "default_rate")
		validators.ensure_positive(self, "default_rate")
