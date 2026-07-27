from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from country_api import create_app
from country_api.database import (
    connect_database,
    data_quality_snapshot,
    list_ingestion_runs,
    summary_snapshot,
)
from country_api.service import refresh_country_data
from country_api.world_bank import FixtureWorldBankClient


FIXTURE_DIRECTORY = Path(__file__).resolve().parents[1] / "data" / "fixtures"


class FailingCountryClient:
    source_name = "failing test source"

    def fetch_country(self, code: str) -> dict:
        raise RuntimeError(f"Source unavailable for {code}")

    def fetch_population(self, code: str, from_year: int, to_year: int) -> list[dict]:
        return []


class ReportingTest(unittest.TestCase):
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

    def test_summary_reports_current_dataset_metrics(self):
        summary = summary_snapshot(self.database_path)
        self.assertEqual(summary["countries"], 3)
        self.assertEqual(summary["populationObservations"], 6)
        self.assertEqual(summary["latestObservationYear"], 2023)
        self.assertEqual(summary["missingPopulationValues"], 0)
        self.assertEqual(summary["countriesWithoutPopulation"], 0)
        self.assertIsNotNone(summary["lastSuccessfulIngestion"])

    def test_data_quality_executes_named_sql_checks(self):
        report = data_quality_snapshot(self.database_path)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["errorViolations"], 0)
        self.assertEqual(report["warningViolations"], 0)
        self.assertEqual(len(report["checks"]), 10)
        self.assertTrue(all(check["passed"] for check in report["checks"]))
        self.assertEqual(
            report["provenance"]["queryFile"],
            "sql/data_quality_queries.sql",
        )

    def test_country_without_population_is_reported_as_warning(self):
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO countries (
                    iso2_code, country_name, source_name, fetched_at
                ) VALUES ('FR', 'France', 'test fixture', '2026-01-01T00:00:00+00:00')
                """
            )

        report = data_quality_snapshot(self.database_path)
        warning = next(
            check
            for check in report["checks"]
            if check["name"] == "countries_without_population"
        )
        self.assertEqual(report["status"], "warning")
        self.assertEqual(warning["violations"], 1)
        self.assertFalse(warning["passed"])

    def test_ingestion_history_records_successful_and_failed_runs(self):
        with self.assertRaises(RuntimeError):
            refresh_country_data(
                self.database_path,
                client=FailingCountryClient(),
                country_codes=["DE"],
                from_year=2022,
                to_year=2023,
            )

        runs = list_ingestion_runs(self.database_path, limit=10)
        self.assertEqual([run["status"] for run in runs[:2]], ["failed", "success"])
        self.assertIn("Source unavailable", runs[0]["errorMessage"])

    def test_reporting_endpoints_return_documented_shapes(self):
        summary_response = self.client.get("/api/v1/summary")
        self.assertEqual(summary_response.status_code, 200)
        self.assertEqual(summary_response.get_json()["data"]["countries"], 3)

        quality_response = self.client.get("/api/v1/data-quality")
        self.assertEqual(quality_response.status_code, 200)
        self.assertEqual(quality_response.get_json()["data"]["status"], "passed")

        runs_response = self.client.get("/api/v1/ingestion-runs?limit=1")
        self.assertEqual(runs_response.status_code, 200)
        self.assertEqual(runs_response.get_json()["meta"]["count"], 1)
        self.assertEqual(runs_response.get_json()["data"][0]["status"], "success")

    def test_invalid_ingestion_limit_uses_error_contract(self):
        response = self.client.get("/api/v1/ingestion-runs?limit=0")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json()["error"]["code"],
            "invalid_query_parameter",
        )


if __name__ == "__main__":
    unittest.main()
