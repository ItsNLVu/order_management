import frappe

from order_management.order_management.constants import DocTypes


def get_settings():
	"""Order Settings, cached; Frappe clears the cache when the settings are saved."""
	return frappe.get_cached_doc(DocTypes.SETTINGS)
