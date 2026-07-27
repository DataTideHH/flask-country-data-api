from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from country_api import create_app
from country_api.service import refresh_country_data
from country_api.world_bank import FixtureWorldBankClient


FIXTURE_DIRECTORY = Path(__file__).resolve().parents[1] / "data" / "fixtures"


class RoutesAndCliTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "country.sqlite"
        self.app = create_app(
            {
                "TESTING": True,
                "DATABASE_PATH": str(self.database_path),
            }
        )
        refresh_country_data(
            self.database_path,
            client=FixtureWorldBankClient(FIXTURE_DIRECTORY),
            country_codes=["DE", "US", "JP"],
            from_year=2022,
            to_year=2023,
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_root_describes_versioned_endpoints(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["service"], "flask-country-data-api")

    def test_health_reports_database_counts(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["countries"], 3)

    def test_country_list_filters_and_deduplicates_codes(self):
        response = self.client.get("/api/v1/countries?codes=de,US,de&limit=10")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["meta"]["count"], 2)
        self.assertEqual(
            [item["countryCode"] for item in payload["data"]],
            ["DE", "US"],
        )

    def test_country_detail_and_population_history(self):
        detail = self.client.get("/api/v1/countries/DE")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.get_json()["data"]["countryName"], "Germany")

        history = self.client.get(
            "/api/v1/countries/DE/population?from=2022&to=2023"
        )
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.get_json()["meta"]["count"], 2)

    def test_invalid_query_uses_stable_error_contract(self):
        response = self.client.get("/api/v1/countries?codes=DE,123")
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertEqual(payload["error"]["code"], "invalid_query_parameter")
        self.assertIn("message", payload["error"])

    def test_unknown_country_returns_not_found_contract(self):
        response = self.client.get("/api/v1/countries/ZZ")
        self.assertEqual(response.status_code, 404)
        payload = response.get_json()
        self.assertEqual(payload["error"]["code"], "country_not_found")
        self.assertEqual(payload["error"]["details"]["countryCode"], "ZZ")

    def test_invalid_population_range_is_rejected(self):
        response = self.client.get(
            "/api/v1/countries/DE/population?from=2024&to=2022"
        )
        self.assertEqual(response.status_code, 400)

    def test_refresh_cli_supports_versioned_fixtures(self):
        separate_database = Path(self.temporary_directory.name) / "cli.sqlite"
        app = create_app(
            {
                "TESTING": True,
                "DATABASE_PATH": str(separate_database),
            }
        )
        runner = app.test_cli_runner()
        result = runner.invoke(
            args=[
                "refresh-data",
                "--codes",
                "DE,US",
                "--from-year",
                "2022",
                "--to-year",
                "2023",
                "--fixture-dir",
                str(FIXTURE_DIRECTORY),
            ]
        )
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('"countriesLoaded": 2', result.output)
        self.assertIn('"observationsLoaded": 4', result.output)


if __name__ == "__main__":
    unittest.main()
