from unittest import TestCase

from order_management.order_management.services.pricing import compute_amount


class TestPricing(TestCase):
	def test_amount_is_quantity_times_rate(self):
		self.assertEqual(compute_amount(3, 1_250_000), 3_750_000)

	def test_amount_is_rounded_to_precision(self):
		self.assertEqual(compute_amount(3, 0.3333, 2), 1.0)
		self.assertEqual(compute_amount(1, 10.4, 0), 10)
