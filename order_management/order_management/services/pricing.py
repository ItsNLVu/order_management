from frappe.utils import flt


def compute_amount(qty: float, rate: float, precision: int | None = None) -> float:
	return flt(flt(qty) * flt(rate), precision)
