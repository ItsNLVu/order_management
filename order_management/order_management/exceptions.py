import frappe


class OrderRuleError(frappe.ValidationError):
	"""Base class for every business rule this app enforces."""


class InvalidTransitionError(OrderRuleError):
	pass


class TransitionNotPermittedError(OrderRuleError):
	pass


class OrderLockedError(OrderRuleError):
	pass
