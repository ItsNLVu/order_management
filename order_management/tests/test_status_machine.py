from frappe.tests.utils import FrappeTestCase

from order_management.order_management.constants import OrderAction, OrderStatus, Role
from order_management.order_management.exceptions import (
	InvalidTransitionError,
	TransitionNotPermittedError,
)
from order_management.order_management.services import status_machine as sm

MANAGER = [Role.ORDER_MANAGER.value]
USER = [Role.ORDER_USER.value]


class TestStatusMachine(FrappeTestCase):
	def test_only_new_is_open(self):
		self.assertFalse(sm.is_final(OrderStatus.NEW.value))
		self.assertTrue(sm.is_final(OrderStatus.DELIVERED.value))
		self.assertTrue(sm.is_final(OrderStatus.CANCELLED.value))

	def test_allowed_transitions_depend_on_status_and_role(self):
		actions = {t.action for t in sm.allowed_transitions(OrderStatus.NEW.value, MANAGER)}
		self.assertEqual(actions, {OrderAction.DELIVER, OrderAction.CANCEL})
		self.assertEqual(sm.allowed_transitions(OrderStatus.NEW.value, USER), [])
		for final in (OrderStatus.DELIVERED, OrderStatus.CANCELLED):
			self.assertEqual(sm.allowed_transitions(final.value, MANAGER), [])

	def test_every_pair_of_statuses(self):
		allowed = {
			(OrderStatus.NEW, OrderStatus.DELIVERED),
			(OrderStatus.NEW, OrderStatus.CANCELLED),
		}
		for source in OrderStatus:
			for target in OrderStatus:
				if source == target:
					continue
				with self.subTest(source=source, target=target):
					if (source, target) in allowed:
						self.assertEqual(
							sm.get_transition(source.value, target.value, MANAGER).target, target
						)
					else:
						with self.assertRaises(InvalidTransitionError):
							sm.get_transition(source.value, target.value, MANAGER)

	def test_role_is_checked(self):
		with self.assertRaises(TransitionNotPermittedError):
			sm.get_transition(OrderStatus.NEW.value, OrderStatus.DELIVERED.value, USER)

	def test_transition_fields(self):
		self.assertEqual(
			sm.transition_fields(),
			{"delivered_at", "delivered_by", "cancelled_at", "cancelled_by", "cancel_reason"},
		)
