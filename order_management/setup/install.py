import frappe

from order_management.order_management.constants import DocTypes, Role


def before_install():
	ensure_roles()


def after_install():
	ensure_default_settings()


def after_migrate():
	ensure_roles()


def ensure_roles():
	for role in Role:
		if not frappe.db.exists("Role", role.value):
			frappe.get_doc({"doctype": "Role", "role_name": role.value, "desk_access": 1}).insert(
				ignore_permissions=True
			)


def ensure_default_settings():
	# Defaults come from the DocType JSON
	settings = frappe.get_single(DocTypes.SETTINGS)
	for df in settings.meta.fields:
		if df.default is not None and frappe.db.get_single_value(DocTypes.SETTINGS, df.fieldname) is None:
			settings.set(df.fieldname, df.default)
	settings.save(ignore_permissions=True)
