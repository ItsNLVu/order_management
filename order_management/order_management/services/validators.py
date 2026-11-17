"""Reusable checks. Each one stops the save with a translated message when its rule is broken."""

import frappe
from frappe import _
from frappe.model import numeric_fieldtypes
from frappe.utils import cint, cstr, flt

from order_management.order_management.exceptions import OrderLockedError, OrderRuleError, raise_rule


def _label(doc, fieldname: str) -> str:
	return _(doc.meta.get_label(fieldname))


def ensure_positive(doc, *fieldnames: str) -> None:
	for fieldname in fieldnames:
		if flt(doc.get(fieldname)) <= 0:
			raise_rule(OrderRuleError, _("{0} must be greater than 0.").format(_label(doc, fieldname)))


def ensure_whole_number(doc, *fieldnames: str) -> None:
	for fieldname in fieldnames:
		value = flt(doc.get(fieldname))
		if value != cint(value):
			raise_rule(OrderRuleError, _("{0} must be a whole number.").format(_label(doc, fieldname)))


def _column_limit(fieldtype: str) -> float | None:
	"""Largest value the database column of this field type can hold, read from Frappe's type map."""
	db_type, length = frappe.db.type_map.get(fieldtype, (None, None))
	if db_type == "decimal":
		digits, scale = (int(part) for part in length.split(","))
		return 10 ** (digits - scale) - 1
	if db_type == "int":
		return 2**31 - 1
	return None


def ensure_within_limits(doc, *fieldnames: str) -> None:
	"""Reject numbers the database cannot store, before the write fails with a server error."""
	for fieldname in fieldnames:
		df = doc.meta.get_field(fieldname)
		limit = _column_limit(df.fieldtype)
		if limit is not None and abs(flt(doc.get(fieldname))) > limit:
			raise_rule(
				OrderRuleError,
				_("{0} is too large. The largest allowed value is {1}.").format(
					_label(doc, fieldname), frappe.format_value(limit, {"fieldtype": "Int"})
				),
			)


def ensure_active(doctype: str, title: str, is_disabled: bool) -> None:
	if is_disabled:
		raise_rule(
			OrderRuleError,
			_("{0} {1} is disabled. Choose another one or enable it again.").format(_(doctype), title),
		)


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
		raise_rule(OrderLockedError, (message or _("These fields cannot be changed: {0}.")).format(labels))
