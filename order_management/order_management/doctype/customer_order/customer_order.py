# Copyright (c) 2026, Nguyen Long Vu and contributors
# For license information, please see license.txt

"""Customer Order controller.

Thin on purpose: it calls the services in the order Frappe runs its hooks, so every way
of saving (form, REST API, data import, apply_action) goes through the same rules.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, now_datetime

from order_management.order_management.constants import DocTypes, OrderStatus
from order_management.order_management.exceptions import OrderLockedError, OrderRuleError, raise_rule
from order_management.order_management.services import status_machine, validators
from order_management.order_management.services.pricing import compute_amount
from order_management.order_management.services.settings import get_settings


class CustomerOrder(Document):
	def onload(self):
		roles = frappe.get_roles()
		self.set_onload("is_locked", status_machine.is_final(self.status))
		self.set_onload(
			"allowed_actions",
			[
				{
					"action": t.action.value,
					"label": t.label,
					"target": t.target.value,
					"requires_reason": self._reason_required(t),
					# A change into a final status cannot be undone, so the form asks first
					"is_final": status_machine.is_final(t.target.value),
				}
				for t in status_machine.allowed_transitions(self.status, roles)
			],
		)

	def before_insert(self):
		# A new order always starts as New, whatever the client sent.
		self.status = OrderStatus.NEW.value
		for fieldname in status_machine.transition_fields():
			self.set(fieldname, None)

	def validate(self):
		before = self.get_doc_before_save()

		if before and status_machine.is_final(before.status):
			validators.ensure_unchanged(
				self,
				before,
				message=_("This order is {0} and can no longer be changed.").format(_(before.status))
				+ " "
				+ _("Changed: {0}."),
			)
			return

		self.validate_links_active()
		self.set_rate()
		self.normalize_numbers()
		validators.ensure_within_limits(self, "qty", "rate")
		validators.ensure_positive(self, "qty", "rate")
		self.amount = compute_amount(self.qty, self.rate, self.precision("amount"))
		validators.ensure_within_limits(self, "amount")

		if before and before.status != self.status:
			self.apply_transition(before)
		elif before:
			# Outside a transition, the fields a transition owns stay as they are.
			validators.ensure_unchanged(self, before, status_machine.transition_fields())

	def on_trash(self):
		if status_machine.is_final(self.status):
			raise_rule(
				OrderLockedError,
				_("Only orders in status {0} can be deleted.").format(_(OrderStatus.NEW.value)),
			)

	def validate_links_active(self):
		for fieldname, doctype in (("customer", DocTypes.CUSTOMER), ("item", DocTypes.ITEM)):
			name = self.get(fieldname)
			# An empty link is reported by Frappe's own mandatory check after validate
			if name and (self.is_new() or self.has_value_changed(fieldname)):
				title_field = frappe.get_meta(doctype).title_field
				disabled, title = frappe.get_cached_value(doctype, name, ["disabled", title_field])
				validators.ensure_active(doctype, title or name, disabled)

	def set_rate(self):
		"""When Order Settings forbid changing the rate, it always comes from the item."""
		if self.item and not get_settings().allow_rate_override:
			self.rate = frappe.get_cached_value(DocTypes.ITEM, self.item, "default_rate")

	def normalize_numbers(self):
		"""Store what the user will see: a whole quantity and a rate rounded like the currency.

		Rounding first means a rate such as 0.1 VND is checked as 0 and rejected, instead of
		passing the check and producing an amount of 0.
		"""
		validators.ensure_whole_number(self, "qty")
		self.qty = cint(self.qty)
		self.rate = flt(self.rate, self.precision("rate"))

	def apply_transition(self, before):
		transition = status_machine.get_transition(before.status, self.status, frappe.get_roles())

		# Only this transition's own fields may change along with the status.
		other_fields = status_machine.transition_fields() - {
			transition.at_field,
			transition.by_field,
			transition.reason_field,
		}
		validators.ensure_unchanged(self, before, other_fields)

		if self._reason_required(transition) and not (self.get(transition.reason_field) or "").strip():
			raise_rule(OrderRuleError, _("Please enter a reason for this change."))

		self.set(transition.at_field, now_datetime())
		self.set(transition.by_field, frappe.session.user)

	@staticmethod
	def _reason_required(transition) -> bool:
		return bool(transition.reason_setting and get_settings().get(transition.reason_setting))


def on_doctype_update():
	# The daily revenue report filters by status and a creation date range.
	frappe.db.add_index(DocTypes.ORDER, ["status", "creation"])
