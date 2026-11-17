"""Shared builders for tests, so each test states only what matters to it."""

from contextlib import contextmanager

import frappe
from frappe.utils import random_string

from order_management.api import apply_action
from order_management.order_management.constants import DocTypes, OrderAction, Role


def make_customer(**values) -> str:
	return (
		frappe.get_doc(
			{"doctype": DocTypes.CUSTOMER, "customer_name": f"Test Customer {random_string(6)}", **values}
		)
		.insert()
		.name
	)


def make_item(default_rate: float = 100_000, **values) -> str:
	return (
		frappe.get_doc(
			{
				"doctype": DocTypes.ITEM,
				"item_name": f"Test Item {random_string(6)}",
				"default_rate": default_rate,
				**values,
			}
		)
		.insert()
		.name
	)


def make_order(qty: int = 2, rate: float = 100_000, **values):
	# Build masters only when the test did not pass its own (setdefault would build them anyway)
	if "customer" not in values:
		values["customer"] = make_customer()
	if "item" not in values:
		values["item"] = make_item()
	return frappe.get_doc({"doctype": DocTypes.ORDER, "qty": qty, "rate": rate, **values}).insert()


def act(order, action: OrderAction, reason: str | None = None):
	"""Apply an action through the public API, then return the reloaded order."""
	apply_action(order.name, action.value, reason)
	return frappe.get_doc(DocTypes.ORDER, order.name)


def user_email_for(role: Role) -> str:
	return f"test-{role.name.lower().replace('_', '-')}@order.test"


def ensure_test_user(role: Role) -> str:
	email = user_email_for(role)
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": role.value,
				"send_welcome_email": 0,
				"roles": [{"role": role.value}],
			}
		).insert(ignore_permissions=True)
	return email


@contextmanager
def as_user(role: Role):
	email = ensure_test_user(role)
	frappe.set_user(email)
	try:
		yield email
	finally:
		frappe.set_user("Administrator")


@contextmanager
def override_settings(**values):
	settings = frappe.get_single(DocTypes.SETTINGS)
	previous = {key: settings.get(key) for key in values}
	settings.update(values)
	settings.save(ignore_permissions=True)
	try:
		yield
	finally:
		settings.update(previous)
		settings.save(ignore_permissions=True)


def backdate(order_name: str, created) -> None:
	frappe.db.set_value(DocTypes.ORDER, order_name, "creation", created, update_modified=False)
