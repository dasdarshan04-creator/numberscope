import math
import unittest

from numberscope.trilateration import estimate_demo_position, solve


class EstimateDemoPositionTests(unittest.TestCase):
    def test_recovers_point_from_consistent_sample_ranges(self):
        ranges = (math.sqrt(18), math.sqrt(34), math.sqrt(17))

        x, y = estimate_demo_position(ranges)

        self.assertAlmostEqual(x, 3.0)
        self.assertAlmostEqual(y, 3.0)

    def test_rejects_non_positive_sample_range(self):
        with self.assertRaises(ValueError):
            estimate_demo_position((0.0, 5.0, 4.0))

    def test_rejects_non_finite_range(self):
        with self.assertRaises(ValueError):
            estimate_demo_position((math.inf, 5.0, 4.0))

    def test_consistent_ranges_have_near_zero_rms(self):
        result = solve((math.sqrt(18), math.sqrt(34), math.sqrt(17)))

        self.assertTrue(result.is_consistent)
        self.assertAlmostEqual(result.rms_error, 0.0)

    def test_inconsistent_ranges_report_error(self):
        result = solve((4.2, 9.5, 4.1))

        self.assertFalse(result.is_consistent)
        self.assertGreater(result.rms_error, 0.0)


if __name__ == "__main__":
    unittest.main()
