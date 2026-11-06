import unittest

from numberscope import analyse_number
from numberscope.analysis import NOT_AVAILABLE


class AnalyseNumberTests(unittest.TestCase):
    def test_valid_indian_mobile(self):
        report = analyse_number("+919876543210")

        self.assertEqual(report.region_code, "IN")
        self.assertEqual(report.country_calling_code, "+91")
        self.assertTrue(report.possible)
        self.assertTrue(report.valid_range)
        self.assertEqual(report.e164, "+919876543210")

    def test_region_fallback_for_non_plus_input(self):
        plus = analyse_number("+919876543210")
        local = analyse_number("9876543210", default_region="IN")

        self.assertEqual(local.e164, plus.e164)

    def test_us_number(self):
        report = analyse_number("+14155552671")

        self.assertEqual(report.region_code, "US")
        self.assertTrue(report.valid_range)

    def test_empty_input_raises(self):
        with self.assertRaises(ValueError):
            analyse_number("   ")

    def test_unparseable_input_raises(self):
        with self.assertRaises(ValueError):
            analyse_number("not-a-number")

    def test_too_short_is_not_valid(self):
        report = analyse_number("+9112345")

        self.assertFalse(report.valid_range)

    def test_report_is_serialisable(self):
        report = analyse_number("+919876543210")
        data = report.as_dict()

        self.assertIn("metadata_version", data)
        self.assertIn("analysed_at_utc", data)
        self.assertIsInstance(report.as_flat_row()["time_zones"], str)

    def test_time_zones_never_empty(self):
        report = analyse_number("+14155552671")

        self.assertTrue(report.time_zones)
        self.assertNotEqual(report.time_zones, [NOT_AVAILABLE] * 0)


if __name__ == "__main__":
    unittest.main()
