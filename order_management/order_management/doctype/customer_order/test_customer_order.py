# Copyright (c) 2026, Nguyen Long Vu and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime

from order_management.order_management.constants import DocTypes, OrderAction, OrderStatus, Role
from order_management.order_management.exceptions import (
	InvalidTransitionError,
	OrderLockedError,
	OrderRuleError,
	TransitionNotPermittedError,
)
from order_management.tests.factories import (
	act,
	as_user,
	make_customer,
	make_item,
	make_order,
	override_settings,
	user_email_for,
)


class TestCustomerOrder(FrappeTestCase):
	# Amount and server-side checks

	def test_amount_is_computed_on_server(self):
		order = make_order(qty=3, rate=1_000, amount=1)
		self.assertEqual(order.amount, 3_000)

		order.qty = 4
		order.amount = 999_999
		order.save()
		self.assertEqual(order.amount, 4_000)

	def test_quantity_and_rate_must_be_positive(self):
		for values in ({"qty": 0}, {"qty": -1}, {"rate": 0}, {"rate": -5}):
			with self.subTest(**values), self.assertRaises(OrderRuleError):
				make_order(**values)

	def test_rate_is_checked_after_rounding_to_the_currency(self):
		# A rate below the smallest currency unit rounds to 0, so it must not slip through
		with self.assertRaises(OrderRuleError):
			make_order(rate=0.001)

	def test_numbers_the_database_cannot_hold_are_rejected(self):
		for values in ({"qty": 10**10}, {"rate": 10**13}, {"qty": 10**6, "rate": 10**7}):
			with self.subTest(**values), self.assertRaises(OrderRuleError):
				make_order(**values)

	def test_unknown_status_is_named_in_the_error(self):
		order = make_order()
		order.status = "Shipped"
		with self.assertRaises(InvalidTransitionError) as raised:
			order.save()
		self.assertIn("Shipped", str(raised.exception))

	def test_quantity_must_be_whole(self):
		with self.assertRaises(OrderRuleError):
			make_order(qty=1.5)

	def test_disabled_customer_or_item_cannot_be_used(self):
		with self.assertRaises(OrderRuleError):
			make_order(customer=make_customer(disabled=1))
		with self.assertRaises(OrderRuleError):
			make_order(item=make_item(disabled=1))

	def test_missing_customer_or_item_is_a_mandatory_error(self):
		for field in ("customer", "item"):
			with self.subTest(field=field), self.assertRaises(frappe.MandatoryError):
				make_order(**{field: None})

	def test_open_order_stays_usable_after_its_customer_is_disabled(self):
		order = make_order()
		frappe.db.set_value(DocTypes.CUSTOMER, order.customer, "disabled", 1)
		self.assertEqual(act(order, OrderAction.DELIVER).status, OrderStatus.DELIVERED.value)

	def test_rate_comes_from_item_when_override_is_off(self):
		item = make_item(default_rate=50_000)
		with override_settings(allow_rate_override=0):
			order = make_order(item=item, qty=2, rate=1)
		self.assertEqual(order.rate, 50_000)
		self.assertEqual(order.amount, 100_000)

	# Status

	def test_new_order_always_starts_as_new(self):
		order = make_order(status=OrderStatus.DELIVERED.value, delivered_at=now_datetime())
		self.assertEqual(order.status, OrderStatus.NEW.value)
		self.assertIsNone(order.delivered_at)

	def test_deliver_records_time_and_user(self):
		order = act(make_order(), OrderAction.DELIVER)
		self.assertEqual(order.status, OrderStatus.DELIVERED.value)
		self.assertIsNotNone(order.delivered_at)
		self.assertEqual(order.delivered_by, "Administrator")

	def test_cancel_records_reason(self):
		order = act(make_order(), OrderAction.CANCEL, reason="Customer changed their mind")
		self.assertEqual(order.status, OrderStatus.CANCELLED.value)
		self.assertEqual(order.cancel_reason, "Customer changed their mind")
		self.assertIsNotNone(order.cancelled_at)

	def test_cancel_reason_follows_settings(self):
		for reason in (None, "", "   "):
			with self.subTest(reason=reason), self.assertRaises(OrderRuleError):
				act(make_order(), OrderAction.CANCEL, reason=reason)
		with override_settings(require_cancel_reason=0):
			self.assertEqual(act(make_order(), OrderAction.CANCEL).status, OrderStatus.CANCELLED.value)

	def test_status_change_through_plain_save_follows_the_same_rules(self):
		order = make_order()
		order.status = OrderStatus.DELIVERED.value
		order.save()
		self.assertEqual(order.status, OrderStatus.DELIVERED.value)
		self.assertIsNotNone(order.delivered_at)

	def test_transition_fields_cannot_be_set_outside_a_transition(self):
		order = make_order()
		order.delivered_at = now_datetime()
		with self.assertRaises(OrderLockedError):
			order.save()

	def test_final_orders_are_locked(self):
		for action, reason in ((OrderAction.DELIVER, None), (OrderAction.CANCEL, "Duplicate order")):
			with self.subTest(action=action):
				order = act(make_order(), action, reason=reason)

				order.qty += 1
				with self.assertRaises(OrderLockedError):
					order.save()

				order.reload()
				order.status = OrderStatus.NEW.value
				with self.assertRaises(OrderLockedError):
					order.save()

				for other in OrderAction:
					with self.assertRaises(InvalidTransitionError):
						act(order, other, reason="x")

				with self.assertRaises(OrderLockedError):
					frappe.delete_doc(DocTypes.ORDER, order.name)

	def test_new_order_can_be_deleted(self):
		order = make_order()
		frappe.delete_doc(DocTypes.ORDER, order.name)
		self.assertFalse(frappe.db.exists(DocTypes.ORDER, order.name))

	# Roles

	def test_order_user_cannot_deliver_or_cancel(self):
		order = make_order()
		frappe.share.add(DocTypes.ORDER, order.name, user_email_for(Role.ORDER_USER), write=1)
		with as_user(Role.ORDER_USER):
			for action in OrderAction:
				with self.subTest(action=action), self.assertRaises(TransitionNotPermittedError):
					act(order, action, reason="x")

			doc = frappe.get_doc(DocTypes.ORDER, order.name)
			doc.status = OrderStatus.DELIVERED.value
			with self.assertRaises(TransitionNotPermittedError):
				doc.save()

	def test_order_user_can_create_and_edit_new_orders(self):
		customer, item = make_customer(), make_item()
		with as_user(Role.ORDER_USER):
			order = make_order(customer=customer, item=item, qty=1)
			order.qty = 2
			order.save()
		self.assertEqual(order.amount, 200_000)

	def test_order_manager_can_deliver(self):
		order = make_order()
		with as_user(Role.ORDER_MANAGER) as email:
			order = act(order, OrderAction.DELIVER)
		self.assertEqual(order.delivered_by, email)

	def test_form_shows_only_allowed_actions(self):
		order = make_order()
		with as_user(Role.ORDER_USER):
			order.run_method("onload")
			self.assertEqual(order.get_onload().allowed_actions, [])
		with as_user(Role.ORDER_MANAGER):
			order.run_method("onload")
			actions = {
				a["action"]: (a["target"], a["requires_reason"], a["is_final"])
				for a in order.get_onload().allowed_actions
			}
		self.assertEqual(
			actions,
			{
				OrderAction.DELIVER.value: (OrderStatus.DELIVERED.value, False, True),
				OrderAction.CANCEL.value: (OrderStatus.CANCELLED.value, True, True),
			},
		)
