"""Order status rules as data.

Every allowed status change is one row in TRANSITIONS. The controller, the API and the
form buttons all read this table, so adding a status or an action happens here.
"""

from dataclasses import dataclass

from frappe import _

from order_management.order_management.constants import OrderAction, OrderStatus, Role
from order_management.order_management.exceptions import (
	InvalidTransitionError,
	TransitionNotPermittedError,
	raise_rule,
)


@dataclass(frozen=True)
class Transition:
	action: OrderAction
	label: str  # English source text, translated where it is shown
	sources: frozenset[OrderStatus]
	target: OrderStatus
	roles: frozenset[Role]
	at_field: str  # set to the time of the change
	by_field: str  # set to the user who made the change
	reason_field: str | None = None  # holds the reason, when the action takes one
	reason_setting: str | None = None  # Order Settings flag that makes the reason mandatory


TRANSITIONS: dict[OrderAction, Transition] = {
	OrderAction.DELIVER: Transition(
		action=OrderAction.DELIVER,
		label="Mark as Delivered",
		sources=frozenset({OrderStatus.NEW}),
		target=OrderStatus.DELIVERED,
		roles=frozenset({Role.ORDER_MANAGER}),
		at_field="delivered_at",
		by_field="delivered_by",
	),
	OrderAction.CANCEL: Transition(
		action=OrderAction.CANCEL,
		label="Cancel Order",
		sources=frozenset({OrderStatus.NEW}),
		target=OrderStatus.CANCELLED,
		roles=frozenset({Role.ORDER_MANAGER}),
		at_field="cancelled_at",
		by_field="cancelled_by",
		reason_field="cancel_reason",
		reason_setting="require_cancel_reason",
	),
}

# Indicator colour of each status in list and form views.
STATUS_COLORS: dict[OrderStatus, str] = {
	OrderStatus.NEW: "blue",
	OrderStatus.DELIVERED: "green",
	OrderStatus.CANCELLED: "red",
}


def is_final(status: str) -> bool:
	"""A status is final when no transition leaves it."""
	return not any(status in t.sources for t in TRANSITIONS.values())


def transition_fields() -> set[str]:
	"""Fields only a transition may write."""
	fields = set()
	for t in TRANSITIONS.values():
		fields.update({t.at_field, t.by_field})
		if t.reason_field:
			fields.add(t.reason_field)
	return fields


def _allowed_for(transition: Transition, roles: list[str] | set[str]) -> bool:
	return any(role.value in roles for role in transition.roles)


def allowed_transitions(status: str, roles: list[str] | set[str]) -> list[Transition]:
	"""Transitions the given roles may apply to an order in this status."""
	return [t for t in TRANSITIONS.values() if status in t.sources and _allowed_for(t, roles)]


def get_action_transition(action: str, status: str) -> Transition:
	"""Return the transition behind an action, or raise if the action is unknown or not possible now."""
	try:
		transition = TRANSITIONS[OrderAction(action)]
	except ValueError:
		raise_rule(InvalidTransitionError, _("Unknown action: {0}").format(action))
	if status not in transition.sources:
		raise_rule(
			InvalidTransitionError,
			_("{0} is not possible for an order in status {1}.").format(_(transition.label), _(status)),
		)
	return transition


def get_transition(source: str, target: str, roles: list[str] | set[str]) -> Transition:
	"""Return the transition from source to target, or raise if it does not exist or is not allowed."""
	transition = next((t for t in TRANSITIONS.values() if source in t.sources and t.target == target), None)
	if not transition:
		raise_rule(
			InvalidTransitionError, _("Cannot change status from {0} to {1}.").format(_(source), _(target))
		)
	if not _allowed_for(transition, roles):
		allowed_roles = ", ".join(_(role.value) for role in sorted(transition.roles))
		raise_rule(
			TransitionNotPermittedError,
			_("You are not allowed to change status from {0} to {1}. Only {2} can do this.").format(
				_(source), _(target), allowed_roles
			),
		)
	return transition
