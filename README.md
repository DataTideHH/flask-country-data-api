# Flask Country Data API

[![CI](https://github.com/DataTideHH/flask-ai-country-api/actions/workflows/ci.yml/badge.svg)](https://github.com/DataTideHH/flask-ai-country-api/actions/workflows/ci.yml)

**Flask API and reproducible World Bank data workflow with SQLite persistence, request and source validation, explicit provenance, fixture-based tests and cross-platform CI.**

## Purpose

External data is not automatically ready for reliable application use. Source responses must be checked, normalized, stored under stable constraints and exposed through a documented contract.

This project demonstrates that process with country metadata and the World Bank population indicator `SP.POP.TOTL`:

```text
World Bank API
→ source validation
→ normalization
→ transactional SQLite persistence
→ versioned Flask API
```

The Flask routes read from SQLite. They do not call the external source during normal requests. Data retrieval is an explicit refresh process, which keeps API responses predictable and separates ingestion failures from read traffic.

## What the project demonstrates

- Flask application factory and blueprints
- external REST API integration with timeout and error handling
- deterministic fixture mode for local validation and CI
- input, source-shape and semantic validation
- relational SQLite modelling with foreign keys and constraints
- ingestion-run tracking
- versioned API endpoints and stable JSON error responses
- tests covering validation, persistence, routes and CLI behavior
- GitHub Actions on Python 3.12 for Ubuntu and Windows

## Architecture

```text
refresh-data CLI
    |
    +-- WorldBankClient -------- live source
    |
    +-- FixtureWorldBankClient - deterministic fixtures
                |
                v
        validation + normalization
                |
                v
        SQLite transaction
                |
                v
        Flask read API
```

## Data model

### `countries`

Stores one normalized record per ISO-2 country code, including region, income level, capital city, coordinates and provenance.

### `population_observations`

Stores annual `SP.POP.TOTL` observations with a composite key of country code and year.

### `ingestion_runs`

Records refresh status, timestamps, requested countries, loaded rows and failure messages.

See [`sql/schema.sql`](sql/schema.sql) and [`docs/data-quality-notes.md`](docs/data-quality-notes.md).

## API endpoints

| Endpoint | Purpose |
|---|---|
| `GET /` | Service metadata and endpoint overview |
| `GET /health` | Database availability and row counts |
| `GET /api/v1/countries` | List and filter countries |
| `GET /api/v1/countries/<code>` | Read one country with its latest population |
| `GET /api/v1/countries/<code>/population` | Read a population time range |

Examples:

```text
GET /api/v1/countries?codes=DE,US,JP&limit=10
GET /api/v1/countries?region=North%20America
GET /api/v1/countries/DE
GET /api/v1/countries/DE/population?from=2022&to=2023
```

Stable error contract:

```json
{
  "error": {
    "code": "country_not_found",
    "message": "No country was found for code ZZ.",
    "details": {
      "countryCode": "ZZ"
    }
  }
}
```

## Quick start

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

$env:COUNTRY_API_DATABASE = "instance\country-data.sqlite"
python -m flask --app country_api:create_app refresh-data `
  --codes DE,US,JP `
  --from-year 2022 `
  --to-year 2023 `
  --fixture-dir data\fixtures

python -m flask --app country_api:create_app run --port 8080
```

### macOS / Linux

```bash
/usr/local/bin/python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

export COUNTRY_API_DATABASE="instance/country-data.sqlite"
python -m flask --app country_api:create_app refresh-data \
  --codes DE,US,JP \
  --from-year 2022 \
  --to-year 2023 \
  --fixture-dir data/fixtures

python -m flask --app country_api:create_app run --port 8080
```

The fixture command creates a deterministic local database without network access.

## Refresh from the live World Bank API

Remove `--fixture-dir` to use the live source explicitly:

```bash
python -m flask --app country_api:create_app refresh-data \
  --codes DE,US,JP \
  --from-year 2020 \
  --to-year 2024
```

Normal API requests continue to read only from the local SQLite database.

## Tests

```powershell
python -m compileall -q country_api tests main.py
python -m unittest discover -s tests -p "test_*.py" -v
```

The test suite uses versioned World Bank-shaped fixtures and does not perform live HTTP requests.

## Repository structure

```text
flask-country-data-api/
├── .github/workflows/ci.yml
├── country_api/
│   ├── __init__.py
│   ├── cli.py
│   ├── database.py
│   ├── errors.py
│   ├── routes.py
│   ├── service.py
│   ├── validation.py
│   └── world_bank.py
├── data/fixtures/
│   ├── world-bank-countries.json
│   └── world-bank-population.json
├── docs/data-quality-notes.md
├── examples/sample-response.json
├── sql/schema.sql
├── tests/
│   ├── test_routes_and_cli.py
│   ├── test_service_and_database.py
│   └── test_validation.py
├── main.py
├── requirements.txt
└── README.md
```

## Scope boundary

This is a deliberately bounded portfolio project. It demonstrates controlled data ingestion and API delivery without adding an unnecessary frontend, authentication system, container platform or cloud deployment.

The next increment can add richer data-quality reporting, OpenAPI documentation and recruiter-facing architecture evidence without changing the deterministic core.
