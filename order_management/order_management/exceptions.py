import frappe
from frappe import _


class OrderRuleError(frappe.ValidationError):
	"""Base class for every business rule this app enforces."""

	# Title of the error dialog, translated when shown
	title = "Cannot Save"


class InvalidTransitionError(OrderRuleError):
	title = "Status Cannot Change"


class TransitionNotPermittedError(OrderRuleError):
	title = "Not Allowed"


class OrderLockedError(OrderRuleError):
	title = "Order Is Locked"


def raise_rule(exc: type[OrderRuleError], message: str):
	"""Stop the request with a translated message and a dialog title that names the kind of problem."""
	frappe.throw(message, exc=exc, title=_(exc.title))
