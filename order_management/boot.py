from order_management.order_management.services.settings import get_settings
from order_management.order_management.services.status_machine import STATUS_COLORS


def boot_session(bootinfo):
	"""Metadata the client reads instead of hardcoding statuses, colours or settings."""
	settings = get_settings()
	bootinfo.order_management = {
		"status_colors": {status.value: color for status, color in STATUS_COLORS.items()},
		"allow_rate_override": bool(settings.allow_rate_override),
		"report_default_days": settings.report_default_days,
	}
