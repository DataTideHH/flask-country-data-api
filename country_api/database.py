from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"
DATA_QUALITY_QUERIES_PATH = PROJECT_ROOT / "sql" / "data_quality_queries.sql"

DATA_QUALITY_METADATA = {
    "duplicate_country_codes": (
        "error",
        "Country codes must be unique.",
    ),
    "invalid_country_codes": (
        "error",
        "Country codes must contain exactly two uppercase letters.",
    ),
    "missing_country_names": (
        "error",
        "Every country record must contain a non-empty name.",
    ),
    "invalid_coordinates": (
        "error",
        "Stored coordinates must remain inside valid geographic ranges.",
    ),
    "duplicate_population_observations": (
        "error",
        "Each country and year may have at most one population observation.",
    ),
    "orphan_population_observations": (
        "error",
        "Every population observation must reference an existing country.",
    ),
    "negative_population_values": (
        "error",
        "Population values cannot be negative.",
    ),
    "unexpected_indicator_codes": (
        "error",
        "Population rows must use the SP.POP.TOTL indicator.",
    ),
    "countries_without_population": (
        "warning",
        "Countries should normally have at least one population observation.",
    ),
    "incomplete_ingestion_runs": (
        "warning",
        "Ingestion runs should not remain in running status indefinitely.",
    ),
}


@contextmanager
def connect_database(database_path: str | Path) -> Iterator[sqlite3.Connection]:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_database(database_path: str | Path) -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with connect_database(database_path) as connection:
        connection.executescript(schema)


def start_ingestion_run(database_path: str | Path, *, started_at: str, requested: int) -> int:
    with connect_database(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO ingestion_runs (
                started_at, status, countries_requested
            ) VALUES (?, 'running', ?)
            """,
            (started_at, requested),
        )
        return int(cursor.lastrowid)


def complete_ingestion_run(
    database_path: str | Path,
    *,
    run_id: int,
    completed_at: str,
    countries_loaded: int,
    observations_loaded: int,
) -> None:
    with connect_database(database_path) as connection:
        connection.execute(
            """
            UPDATE ingestion_runs
            SET completed_at = ?, status = 'success', countries_loaded = ?,
                observations_loaded = ?, rejected_records = 0, error_message = NULL
            WHERE run_id = ?
            """,
            (completed_at, countries_loaded, observations_loaded, run_id),
        )


def fail_ingestion_run(
    database_path: str | Path,
    *,
    run_id: int,
    completed_at: str,
    error_message: str,
) -> None:
    with connect_database(database_path) as connection:
        connection.execute(
            """
            UPDATE ingestion_runs
            SET completed_at = ?, status = 'failed', error_message = ?
            WHERE run_id = ?
            """,
            (completed_at, error_message[:500], run_id),
        )


def replace_country_data(
    database_path: str | Path,
    *,
    countries: Iterable[dict[str, Any]],
    observations: Iterable[dict[str, Any]],
    country_codes: list[str],
    from_year: int,
    to_year: int,
) -> None:
    country_rows = list(countries)
    observation_rows = list(observations)

    with connect_database(database_path) as connection:
        connection.execute("BEGIN")

        connection.executemany(
            """
            INSERT INTO countries (
                iso2_code, country_name, region_name, income_level, capital_city,
                longitude, latitude, source_name, fetched_at
            ) VALUES (
                :iso2_code, :country_name, :region_name, :income_level, :capital_city,
                :longitude, :latitude, :source_name, :fetched_at
            )
            ON CONFLICT(iso2_code) DO UPDATE SET
                country_name = excluded.country_name,
                region_name = excluded.region_name,
                income_level = excluded.income_level,
                capital_city = excluded.capital_city,
                longitude = excluded.longitude,
                latitude = excluded.latitude,
                source_name = excluded.source_name,
                fetched_at = excluded.fetched_at
            """,
            country_rows,
        )

        connection.executemany(
            """
            DELETE FROM population_observations
            WHERE iso2_code = ? AND observation_year BETWEEN ? AND ?
            """,
            [(code, from_year, to_year) for code in country_codes],
        )

        connection.executemany(
            """
            INSERT INTO population_observations (
                iso2_code, observation_year, population, indicator_code,
                source_name, fetched_at
            ) VALUES (
                :iso2_code, :observation_year, :population, :indicator_code,
                :source_name, :fetched_at
            )
            """,
            observation_rows,
        )


def _country_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "countryCode": row["iso2_code"],
        "countryName": row["country_name"],
        "region": row["region_name"],
        "incomeLevel": row["income_level"],
        "capitalCity": row["capital_city"],
        "coordinates": {
            "longitude": row["longitude"],
            "latitude": row["latitude"],
        },
        "latestPopulation": (
            {
                "year": row["latest_population_year"],
                "value": row["latest_population"],
            }
            if row["latest_population_year"] is not None
            else None
        ),
        "provenance": {
            "source": row["source_name"],
            "fetchedAt": row["fetched_at"],
        },
    }


def list_countries(
    database_path: str | Path,
    *,
    codes: list[str] | None = None,
    region: str | None = None,
    income_level: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    conditions: list[str] = []
    parameters: list[Any] = []

    if codes:
        placeholders = ",".join("?" for _ in codes)
        conditions.append(f"c.iso2_code IN ({placeholders})")
        parameters.extend(codes)
    if region:
        conditions.append("LOWER(c.region_name) = LOWER(?)")
        parameters.append(region.strip())
    if income_level:
        conditions.append("LOWER(c.income_level) = LOWER(?)")
        parameters.append(income_level.strip())

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    parameters.append(limit)

    query = f"""
        SELECT c.*,
               p.observation_year AS latest_population_year,
               p.population AS latest_population
        FROM countries AS c
        LEFT JOIN population_observations AS p
          ON p.iso2_code = c.iso2_code
         AND p.observation_year = (
             SELECT MAX(p2.observation_year)
             FROM population_observations AS p2
             WHERE p2.iso2_code = c.iso2_code
         )
        {where_clause}
        ORDER BY c.iso2_code
        LIMIT ?
    """

    with connect_database(database_path) as connection:
        rows = connection.execute(query, parameters).fetchall()
    return [_country_row_to_dict(row) for row in rows]


def get_country(database_path: str | Path, code: str) -> dict[str, Any] | None:
    rows = list_countries(database_path, codes=[code], limit=1)
    return rows[0] if rows else None


def get_population_history(
    database_path: str | Path,
    *,
    code: str,
    from_year: int,
    to_year: int,
) -> list[dict[str, Any]]:
    with connect_database(database_path) as connection:
        rows = connection.execute(
            """
            SELECT observation_year, population, indicator_code, source_name, fetched_at
            FROM population_observations
            WHERE iso2_code = ? AND observation_year BETWEEN ? AND ?
            ORDER BY observation_year
            """,
            (code, from_year, to_year),
        ).fetchall()

    return [
        {
            "year": row["observation_year"],
            "value": row["population"],
            "indicatorCode": row["indicator_code"],
            "provenance": {
                "source": row["source_name"],
                "fetchedAt": row["fetched_at"],
            },
        }
        for row in rows
    ]


def health_snapshot(database_path: str | Path) -> dict[str, int | str | None]:
    with connect_database(database_path) as connection:
        connection.execute("SELECT 1").fetchone()
        countries = connection.execute("SELECT COUNT(*) FROM countries").fetchone()[0]
        observations = connection.execute(
            "SELECT COUNT(*) FROM population_observations"
        ).fetchone()[0]
        last_run = connection.execute(
            """
            SELECT completed_at
            FROM ingestion_runs
            WHERE status = 'success'
            ORDER BY run_id DESC
            LIMIT 1
            """
        ).fetchone()

    return {
        "status": "ok",
        "countries": int(countries),
        "populationObservations": int(observations),
        "lastSuccessfulIngestion": last_run[0] if last_run else None,
    }


def summary_snapshot(database_path: str | Path) -> dict[str, int | str | None]:
    with connect_database(database_path) as connection:
        row = connection.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM countries) AS countries,
                (SELECT COUNT(*) FROM population_observations) AS observations,
                (SELECT MAX(observation_year) FROM population_observations) AS latest_year,
                (
                    SELECT COUNT(*)
                    FROM population_observations
                    WHERE population IS NULL
                ) AS missing_population_values,
                (
                    SELECT COUNT(*)
                    FROM countries AS c
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM population_observations AS p
                        WHERE p.iso2_code = c.iso2_code
                    )
                ) AS countries_without_population,
                (
                    SELECT completed_at
                    FROM ingestion_runs
                    WHERE status = 'success'
                    ORDER BY run_id DESC
                    LIMIT 1
                ) AS last_successful_ingestion
            """
        ).fetchone()

    return {
        "countries": int(row["countries"]),
        "populationObservations": int(row["observations"]),
        "latestObservationYear": row["latest_year"],
        "missingPopulationValues": int(row["missing_population_values"]),
        "countriesWithoutPopulation": int(row["countries_without_population"]),
        "lastSuccessfulIngestion": row["last_successful_ingestion"],
    }


def list_ingestion_runs(
    database_path: str | Path,
    *,
    limit: int = 20,
) -> list[dict[str, Any]]:
    with connect_database(database_path) as connection:
        rows = connection.execute(
            """
            SELECT run_id, started_at, completed_at, status, countries_requested,
                   countries_loaded, observations_loaded, rejected_records, error_message
            FROM ingestion_runs
            ORDER BY run_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        {
            "runId": row["run_id"],
            "startedAt": row["started_at"],
            "completedAt": row["completed_at"],
            "status": row["status"],
            "countriesRequested": row["countries_requested"],
            "countriesLoaded": row["countries_loaded"],
            "observationsLoaded": row["observations_loaded"],
            "rejectedRecords": row["rejected_records"],
            "errorMessage": row["error_message"],
        }
        for row in rows
    ]


def _load_named_queries(path: Path = DATA_QUALITY_QUERIES_PATH) -> dict[str, str]:
    queries: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []

    def store_current_query() -> None:
        if current_name is None:
            return
        query = "\n".join(current_lines).strip()
        if not query:
            raise ValueError(f"Data-quality query {current_name!r} is empty.")
        queries[current_name] = query

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("-- name:"):
            store_current_query()
            current_name = line.partition(":")[2].strip()
            current_lines = []
        elif current_name is not None:
            current_lines.append(line)

    store_current_query()

    if set(queries) != set(DATA_QUALITY_METADATA):
        missing = sorted(set(DATA_QUALITY_METADATA) - set(queries))
        unexpected = sorted(set(queries) - set(DATA_QUALITY_METADATA))
        raise ValueError(
            "Data-quality query definitions do not match metadata. "
            f"Missing: {missing}; unexpected: {unexpected}."
        )
    return queries


def data_quality_snapshot(database_path: str | Path) -> dict[str, Any]:
    named_queries = _load_named_queries()
    checks: list[dict[str, Any]] = []

    with connect_database(database_path) as connection:
        for name, query in named_queries.items():
            row = connection.execute(query).fetchone()
            violations = int(row["violations"])
            severity, description = DATA_QUALITY_METADATA[name]
            checks.append(
                {
                    "name": name,
                    "severity": severity,
                    "description": description,
                    "violations": violations,
                    "passed": violations == 0,
                }
            )

    error_violations = sum(
        check["violations"] for check in checks if check["severity"] == "error"
    )
    warning_violations = sum(
        check["violations"] for check in checks if check["severity"] == "warning"
    )

    if error_violations:
        status = "failed"
    elif warning_violations:
        status = "warning"
    else:
        status = "passed"

    return {
        "status": status,
        "errorViolations": error_violations,
        "warningViolations": warning_violations,
        "checks": checks,
        "provenance": {
            "queryFile": "sql/data_quality_queries.sql",
            "lastSuccessfulIngestion": summary_snapshot(database_path)[
                "lastSuccessfulIngestion"
            ],
        },
    }
