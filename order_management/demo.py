"""Demo data for reviewers: two users (one per role), a few customers and items, and orders
spread over the last days so the daily revenue report has something to show.

	bench --site <site> execute order_management.demo.create_demo_data
"""

import random

import frappe
from frappe.utils import add_to_date, now_datetime

from order_management.api import apply_action
from order_management.order_management.constants import DocTypes, OrderAction, Role

DEMO_PASSWORD = "Demo@2026"
DEMO_USERS = {
	"sales@order.test": ("Sales Demo", Role.ORDER_USER),
	"manager@order.test": ("Manager Demo", Role.ORDER_MANAGER),
}
CUSTOMERS = [
	("Công ty Nội thất An Phát", "0901000001"),
	("Cửa hàng Gỗ Việt", "0901000002"),
	("Khách sạn Sông Hàn", "0901000003"),
	("Văn phòng Sao Mai", "0901000004"),
]
ITEMS = [
	("Bàn làm việc gỗ sồi", 2_450_000),
	("Ghế xoay văn phòng", 1_190_000),
	("Tủ hồ sơ 3 ngăn", 3_200_000),
	("Kệ sách 5 tầng", 890_000),
]


def create_demo_data(days: int = 10, orders_per_day: int = 3, seed: int = 7):
	rng = random.Random(seed)
	set_regional_defaults()
	for email, (first_name, role) in DEMO_USERS.items():
		ensure_user(email, first_name, role)

	customers = [ensure_master(DocTypes.CUSTOMER, "customer_name", n, phone=p) for n, p in CUSTOMERS]
	items = [ensure_master(DocTypes.ITEM, "item_name", n, default_rate=r) for n, r in ITEMS]
	rates = dict(frappe.get_all(DocTypes.ITEM, fields=["name", "default_rate"], as_list=True))

	for day in range(days - 1, -1, -1):
		created = add_to_date(now_datetime(), days=-day, hours=-rng.randint(0, 6))
		for _ in range(orders_per_day):
			order = frappe.get_doc(
				{
					"doctype": DocTypes.ORDER,
					"customer": rng.choice(customers),
					"item": (item := rng.choice(items)),
					"rate": rates[item],
					"qty": rng.randint(1, 5),
				}
			).insert()
			# Backdate so the report shows several days. Status changes still go through the rules.
			frappe.db.set_value(DocTypes.ORDER, order.name, "creation", created, update_modified=False)
			outcome = rng.random()
			if day > 0 and outcome < 0.7:
				apply_action(order.name, OrderAction.DELIVER.value)
			elif day > 0 and outcome < 0.85:
				apply_action(order.name, OrderAction.CANCEL.value, reason="Khách đổi ý")

	frappe.db.commit()
	print(f"Demo data ready. Users: {', '.join(DEMO_USERS)} (password {DEMO_PASSWORD})")


REGIONAL_DEFAULTS = {
	"time_zone": "Asia/Ho_Chi_Minh",
	"currency": "VND",
	"number_format": "#.###",
	"date_format": "dd-mm-yyyy",
}


def set_regional_defaults():
	"""Vietnam time zone and VND formatting for the demo site."""
	settings = frappe.get_single("System Settings")
	settings.update(REGIONAL_DEFAULTS)
	settings.language = settings.language or "en"  # empty only when the setup wizard was skipped
	settings.save(ignore_permissions=True)
	for key, value in REGIONAL_DEFAULTS.items():  # what the client reads at boot
		frappe.db.set_default(key, value)
	frappe.db.set_value("Currency", "VND", {"symbol": "₫", "symbol_on_right": 1, "enabled": 1})


def ensure_user(email: str, first_name: str, role: Role):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first_name,
				"language": "vi",
				"send_welcome_email": 0,
				"roles": [{"role": role.value}],
			}
		).insert(ignore_permissions=True)
	from frappe.utils.password import update_password

	update_password(email, DEMO_PASSWORD)


def ensure_master(doctype: str, title_field: str, title: str, **values) -> str:
	name = frappe.db.get_value(doctype, {title_field: title})
	if name:
		return name
	return frappe.get_doc({"doctype": doctype, title_field: title, **values}).insert().name
