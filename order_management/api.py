"""One endpoint for every status action. The rules themselves run in the controller."""

import frappe
from frappe import _

from order_management.order_management.constants import DocTypes
from order_management.order_management.services.status_machine import get_action_transition


@frappe.whitelist(methods=["POST"])
def apply_action(order: str | None = None, action: str | None = None, reason: str | None = None) -> dict:
	if not order or not action:
		frappe.throw(_("Both order and action are required."), frappe.MandatoryError)

	# Lock the row so two people acting on the same order are handled one after the other.
	doc = frappe.get_doc(DocTypes.ORDER, order, for_update=True)
	doc.check_permission("write")

	transition = get_action_transition(action, doc.status)
	doc.status = transition.target.value
	if transition.reason_field and reason is not None:
		doc.set(transition.reason_field, reason)
	doc.save()
	return doc.as_dict()
