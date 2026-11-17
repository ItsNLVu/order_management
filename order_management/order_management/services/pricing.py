from frappe.utils import flt


def compute_amount(qty: float, rate: float, precision: int | None = None) -> float:
	"""Line amount. The only place the order total is calculated."""
	return flt(flt(qty) * flt(rate), precision)
