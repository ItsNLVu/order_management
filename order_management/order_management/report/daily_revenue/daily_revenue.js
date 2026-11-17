// Copyright (c) 2026, Nguyen Long Vu and contributors
// For license information, please see license.txt

// The default range length comes from Order Settings (sent at boot), not from this file.
const default_days = () => order_management.meta().report_default_days || 30;

frappe.query_reports["Daily Revenue"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.add_days(frappe.datetime.get_today(), 1 - default_days()),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.get_today(),
		},
	],
};
