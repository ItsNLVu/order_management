frappe.listview_settings["Customer Order"] = {
	add_fields: ["status"],
	get_indicator: (doc) => order_management.status_indicator(doc.status),
};
