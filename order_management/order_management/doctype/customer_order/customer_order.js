// Copyright (c) 2026, Nguyen Long Vu and contributors
// For license information, please see license.txt

// Amount here is a preview; the server recalculates it on save.

frappe.ui.form.on("Customer Order", {
	setup(frm) {
		const only_active = () => ({ filters: { disabled: 0 } });
		frm.set_query("customer", only_active);
		frm.set_query("item", only_active);
	},

	refresh(frm) {
		hide_timezone_notes(frm);
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

// All times are Vietnam time. Frappe writes the timezone into the description, so clear both.
function hide_timezone_notes(frm) {
	for (const df of frm.meta.fields.filter((df) => df.fieldtype === "Datetime")) {
		frm.set_df_property(df.fieldname, "hide_timezone", 1);
		frm.set_df_property(df.fieldname, "description", "");
	}
}

function lock_form(frm) {
	frm.disable_save();
	// frm.set_read_only() does not redraw the inputs, so mark each field instead
	for (const df of frm.meta.fields) {
		if (frappe.model.no_value_type.includes(df.fieldtype)) continue;
		frm.set_df_property(df.fieldname, "read_only", 1);
		if (df.description) frm.set_df_property(df.fieldname, "description", "");
	}
	frm.set_intro(__("This order is {0} and can no longer be changed.", [__(frm.doc.status)]));
}

function add_action_buttons(frm) {
	if (frm.is_new() || frm.is_dirty()) return;

	for (const action of frm.doc.__onload?.allowed_actions || []) {
		frm.add_custom_button(__(action.label), () => run_action(frm, action));
	}
}

function run_action(frm, { action, label, target, requires_reason, is_final }) {
	const message = [__("Change order {0} to {1}?", [frm.doc.name, __(target)])];
	if (is_final) message.push(__("After this the order can no longer be changed."));

	const dialog = new frappe.ui.Dialog({
		title: __(label),
		fields: [
			{
				fieldtype: "HTML",
				options: `<p>${frappe.utils.escape_html(message.join(" "))}</p>`,
			},
			...(requires_reason
				? [{ fieldname: "reason", fieldtype: "Small Text", label: __("Reason"), reqd: 1 }]
				: []),
		],
		primary_action_label: __(label),
		primary_action: ({ reason }) => {
			dialog.hide();
			order_management.apply_action(frm, action, reason);
		},
		secondary_action_label: __("Go Back"),
		secondary_action: () => dialog.hide(),
	});
	dialog.show();
}
