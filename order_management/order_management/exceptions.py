import frappe
from frappe import _


class OrderRuleError(frappe.ValidationError):
	# Error dialog title, translated when shown
	title = "Cannot Save"


class InvalidTransitionError(OrderRuleError):
	title = "Status Cannot Change"


class TransitionNotPermittedError(OrderRuleError):
	title = "Not Allowed"


class OrderLockedError(OrderRuleError):
	title = "Order Is Locked"


def raise_rule(exc: type[OrderRuleError], message: str):
	frappe.throw(message, exc=exc, title=_(exc.title))
