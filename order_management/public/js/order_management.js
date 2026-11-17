// Shared by the order form, list view and report. Colours and settings come from boot.py.

frappe.provide("order_management");

order_management.meta = () => frappe.boot.order_management || {};

order_management.status_indicator = (status) => [
	__(status),
	order_management.meta().status_colors?.[status] || "gray",
	`status,=,${status}`,
];

order_management.apply_action = (frm, action, reason) =>
	frappe
		.call({
			method: "order_management.api.apply_action",
			args: { order: frm.doc.name, action, reason },
			freeze: true,
		})
		.then(() => frm.reload_doc());
