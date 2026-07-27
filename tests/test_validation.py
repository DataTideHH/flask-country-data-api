from __future__ import annotations

import unittest

from country_api.validation import (
    InputValidationError,
    SourceValidationError,
    normalize_country_codes,
    normalize_country_record,
    normalize_population_record,
    parse_limit,
    parse_year_range,
)


class ValidationTest(unittest.TestCase):
    def test_country_codes_are_trimmed_uppercased_and_deduplicated(self):
        self.assertEqual(normalize_country_codes(" de,US,de , jp "), ["DE", "US", "JP"])

    def test_missing_country_codes_are_rejected(self):
        with self.assertRaises(InputValidationError):
            normalize_country_codes("  ")

    def test_invalid_country_code_is_rejected(self):
        with self.assertRaises(InputValidationError):
            normalize_country_codes("DE,123")

    def test_too_many_country_codes_are_rejected(self):
        with self.assertRaises(InputValidationError):
            normalize_country_codes("DE,US,JP", max_codes=2)

    def test_limit_validation(self):
        self.assertEqual(parse_limit("25"), 25)
        with self.assertRaises(InputValidationError):
            parse_limit("0")
        with self.assertRaises(InputValidationError):
            parse_limit("many")

    def test_year_range_validation(self):
        self.assertEqual(
            parse_year_range("2022", "2023", default_from=2020, default_to=2024),
            (2022, 2023),
        )
        with self.assertRaises(InputValidationError):
            parse_year_range("2024", "2022", default_from=2020, default_to=2024)

    def test_country_source_code_must_match_request(self):
        raw = {
            "iso2Code": "US",
            "name": "United States",
            "region": {"value": "North America"},
            "incomeLevel": {"value": "High income"},
        }
        with self.assertRaises(SourceValidationError):
            normalize_country_record(
                raw,
                expected_code="DE",
                source_name="fixture",
                fetched_at="2026-01-01T00:00:00+00:00",
            )

    def test_population_null_is_preserved_and_negative_is_rejected(self):
        raw = {
            "indicator": {"id": "SP.POP.TOTL"},
            "country": {"id": "DE"},
            "date": "2023",
            "value": None,
        }
        normalized = normalize_population_record(
            raw,
            expected_code="DE",
            source_name="fixture",
            fetched_at="2026-01-01T00:00:00+00:00",
        )
        self.assertIsNone(normalized["population"])

        raw["value"] = -1
        with self.assertRaises(SourceValidationError):
            normalize_population_record(
                raw,
                expected_code="DE",
                source_name="fixture",
                fetched_at="2026-01-01T00:00:00+00:00",
            )


if __name__ == "__main__":
    unittest.main()
