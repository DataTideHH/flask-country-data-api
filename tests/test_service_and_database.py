from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from country_api.database import (
    connect_database,
    get_country,
    get_population_history,
    health_snapshot,
)
from country_api.service import refresh_country_data
from country_api.world_bank import FixtureWorldBankClient


FIXTURE_DIRECTORY = Path(__file__).resolve().parents[1] / "data" / "fixtures"


class ServiceAndDatabaseTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "country.sqlite"
        self.client = FixtureWorldBankClient(FIXTURE_DIRECTORY)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def refresh(self):
        return refresh_country_data(
            self.database_path,
            client=self.client,
            country_codes=["DE", "US", "JP"],
            from_year=2022,
            to_year=2023,
        )

    def test_fixture_refresh_builds_expected_relational_data(self):
        result = self.refresh()
        self.assertEqual(result["countriesLoaded"], 3)
        self.assertEqual(result["observationsLoaded"], 6)

        snapshot = health_snapshot(self.database_path)
        self.assertEqual(snapshot["countries"], 3)
        self.assertEqual(snapshot["populationObservations"], 6)
        self.assertIsNotNone(snapshot["lastSuccessfulIngestion"])

    def test_country_detail_contains_latest_population(self):
        self.refresh()
        country = get_country(self.database_path, "DE")
        self.assertIsNotNone(country)
        self.assertEqual(country["countryName"], "Germany")
        self.assertEqual(country["latestPopulation"]["year"], 2023)
        self.assertEqual(country["latestPopulation"]["value"], 84482267)

    def test_population_history_is_ordered(self):
        self.refresh()
        history = get_population_history(
            self.database_path,
            code="US",
            from_year=2022,
            to_year=2023,
        )
        self.assertEqual([item["year"] for item in history], [2022, 2023])

    def test_foreign_keys_are_enforced(self):
        self.refresh()
        with connect_database(self.database_path) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    """
                    INSERT INTO population_observations (
                        iso2_code, observation_year, population, indicator_code,
                        source_name, fetched_at
                    ) VALUES ('ZZ', 2023, 1, 'SP.POP.TOTL', 'test', 'now')
                    """
                )


if __name__ == "__main__":
    unittest.main()
