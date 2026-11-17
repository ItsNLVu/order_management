// Copyright (c) 2026, Nguyen Long Vu and contributors
// For license information, please see license.txt

// The form only draws what the server allows. Amount here is a preview: the server
// recalculates it on save, and every rule is checked again there.

frappe.ui.form.on("Customer Order", {
	setup(frm) {
		const only_active = () => ({ filters: { disabled: 0 } });
		frm.set_query("customer", only_active);
		frm.set_query("item", only_active);
	},

	refresh(frm) {
		frm.set_df_property("rate", "read_only", !order_management.meta().allow_rate_override);
		if (!frm.is_new()) {
			frm.page.set_indicator(
				...order_management.status_indicator(frm.doc.status).slice(0, 2)
			);
		}
		if (frm.doc.__onload?.is_locked) lock_form(frm);
		add_action_buttons(frm);
	},

	async item(frm) {
		if (!frm.doc.item) return;
		const { message } = await frappe.db.get_value("Order Item", frm.doc.item, "default_rate");
		await frm.set_value("rate", message?.default_rate);
	},

	qty: update_amount_preview,
	rate: update_amount_preview,
});

function update_amount_preview(frm) {
	frm.set_value("amount", flt(frm.doc.qty) * flt(frm.doc.rate));
}

function lock_form(frm) {
	frm.disable_save();
	frm.set_read_only();
	frm.set_intro(__("This order is {0} and can no longer be changed.", [__(frm.doc.status)]));
}

function add_action_buttons(frm) {
	if (frm.is_new() || frm.is_dirty()) return;

	for (const { action, label, requires_reason } of frm.doc.__onload?.allowed_actions || []) {
		frm.add_custom_button(__(label), () =>
			requires_reason
				? ask_reason(frm, action, label)
				: order_management.apply_action(frm, action)
		);
	}
}

function ask_reason(frm, action, label) {
	frappe.prompt(
		{ fieldname: "reason", fieldtype: "Small Text", label: __("Reason"), reqd: 1 },
		({ reason }) => order_management.apply_action(frm, action, reason),
		__(label),
		__("Confirm")
	);
}
