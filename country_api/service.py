from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from country_api.database import (
    complete_ingestion_run,
    fail_ingestion_run,
    init_database,
    replace_country_data,
    start_ingestion_run,
)
from country_api.validation import normalize_country_record, normalize_population_record


class CountrySourceClient(Protocol):
    source_name: str

    def fetch_country(self, code: str) -> dict:
        ...

    def fetch_population(self, code: str, from_year: int, to_year: int) -> list[dict]:
        ...


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def refresh_country_data(
    database_path: str | Path,
    *,
    client: CountrySourceClient,
    country_codes: list[str],
    from_year: int,
    to_year: int,
) -> dict[str, int | str]:
    init_database(database_path)
    started_at = utc_timestamp()
    run_id = start_ingestion_run(
        database_path,
        started_at=started_at,
        requested=len(country_codes),
    )

    countries: list[dict] = []
    observations: list[dict] = []

    try:
        for code in country_codes:
            raw_country = client.fetch_country(code)
            countries.append(
                normalize_country_record(
                    raw_country,
                    expected_code=code,
                    source_name=client.source_name,
                    fetched_at=started_at,
                )
            )

            for raw_observation in client.fetch_population(code, from_year, to_year):
                observations.append(
                    normalize_population_record(
                        raw_observation,
                        expected_code=code,
                        source_name=client.source_name,
                        fetched_at=started_at,
                    )
                )

        replace_country_data(
            database_path,
            countries=countries,
            observations=observations,
            country_codes=country_codes,
            from_year=from_year,
            to_year=to_year,
        )

        completed_at = utc_timestamp()
        complete_ingestion_run(
            database_path,
            run_id=run_id,
            completed_at=completed_at,
            countries_loaded=len(countries),
            observations_loaded=len(observations),
        )
    except Exception as exc:
        fail_ingestion_run(
            database_path,
            run_id=run_id,
            completed_at=utc_timestamp(),
            error_message=str(exc),
        )
        raise

    return {
        "runId": run_id,
        "status": "success",
        "countriesLoaded": len(countries),
        "observationsLoaded": len(observations),
        "fromYear": from_year,
        "toYear": to_year,
        "completedAt": completed_at,
    }
