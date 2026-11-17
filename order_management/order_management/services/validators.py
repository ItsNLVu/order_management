"""Reusable checks. Each one raises with a translated message when the rule is broken."""

import frappe
from frappe import _
from frappe.model import numeric_fieldtypes
from frappe.utils import cint, cstr, flt

from order_management.order_management.exceptions import OrderLockedError, OrderRuleError


def _label(doc, fieldname: str) -> str:
	return _(doc.meta.get_label(fieldname))


def ensure_positive(doc, *fieldnames: str) -> None:
	for fieldname in fieldnames:
		if flt(doc.get(fieldname)) <= 0:
			frappe.throw(_("{0} must be greater than 0.").format(_label(doc, fieldname)), exc=OrderRuleError)


def ensure_whole_number(doc, *fieldnames: str) -> None:
	for fieldname in fieldnames:
		value = flt(doc.get(fieldname))
		if value != cint(value):
			frappe.throw(_("{0} must be a whole number.").format(_label(doc, fieldname)), exc=OrderRuleError)


def ensure_active(doctype: str, name: str, is_disabled: bool) -> None:
	if is_disabled:
		frappe.throw(_("{0} {1} is disabled.").format(_(doctype), name), exc=OrderRuleError)


def _normalize(df, value):
	return flt(value) if df.fieldtype in numeric_fieldtypes else cstr(value)


def changed_fields(doc, before, fieldnames: set[str] | None = None) -> list[str]:
	"""Fields whose value differs from the saved version, compared by field type."""
	changed = []
	for df in doc.meta.fields:
		if fieldnames is not None and df.fieldname not in fieldnames:
			continue
		if df.fieldtype in frappe.model.no_value_fields:
			continue
		if _normalize(df, doc.get(df.fieldname)) != _normalize(df, before.get(df.fieldname)):
			changed.append(df.fieldname)
	return changed


def ensure_unchanged(doc, before, fieldnames: set[str] | None = None, message: str | None = None) -> None:
	changed = changed_fields(doc, before, fieldnames)
	if changed:
		labels = ", ".join(_label(doc, f) for f in changed)
		frappe.throw(
			(message or _("These fields cannot be changed: {0}.")).format(labels), exc=OrderLockedError
		)
