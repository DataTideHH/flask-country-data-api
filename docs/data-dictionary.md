# Data Dictionary

## `countries`

| Column | Type | Null | Key / constraint | Meaning |
|---|---|---:|---|---|
| `iso2_code` | TEXT | No | Primary key; two uppercase characters | ISO-2-style country identifier used by the API |
| `country_name` | TEXT | No | Non-empty | Normalized country display name |
| `region_name` | TEXT | Yes | — | World Bank region name |
| `income_level` | TEXT | Yes | — | World Bank income classification |
| `capital_city` | TEXT | Yes | — | Capital city from the source response |
| `longitude` | REAL | Yes | `-180` to `180` | Capital-city longitude where supplied |
| `latitude` | REAL | Yes | `-90` to `90` | Capital-city latitude where supplied |
| `source_name` | TEXT | No | — | Source label used for the stored record |
| `fetched_at` | TEXT | No | ISO-8601 UTC timestamp | Time at which the source record was retrieved or loaded |

## `population_observations`

| Column | Type | Null | Key / constraint | Meaning |
|---|---|---:|---|---|
| `iso2_code` | TEXT | No | Composite primary key; foreign key | Country identifier referencing `countries.iso2_code` |
| `observation_year` | INTEGER | No | Composite primary key; year >= 1960 | Calendar year of the observation |
| `population` | INTEGER | Yes | Non-negative | Population value; `NULL` means the source supplied no value |
| `indicator_code` | TEXT | No | Must equal `SP.POP.TOTL` | World Bank total-population indicator |
| `source_name` | TEXT | No | — | Source label used for the observation |
| `fetched_at` | TEXT | No | ISO-8601 UTC timestamp | Time at which the observation was retrieved or loaded |

## `ingestion_runs`

| Column | Type | Null | Key / constraint | Meaning |
|---|---|---:|---|---|
| `run_id` | INTEGER | No | Primary key, auto-increment | Internal identifier for one refresh invocation |
| `started_at` | TEXT | No | ISO-8601 UTC timestamp | Start time of the refresh run |
| `completed_at` | TEXT | Yes | ISO-8601 UTC timestamp | Completion or failure time |
| `status` | TEXT | No | `running`, `success`, `failed` | Current/final run state |
| `countries_requested` | INTEGER | No | Non-negative | Number of distinct requested country codes |
| `countries_loaded` | INTEGER | No | Non-negative | Number of validated country rows persisted |
| `observations_loaded` | INTEGER | No | Non-negative | Number of validated population rows persisted |
| `rejected_records` | INTEGER | No | Non-negative | Reserved count for explicitly rejected source records |
| `error_message` | TEXT | Yes | Truncated to 500 characters by the application | Failure context for unsuccessful runs |

## API naming convention

SQLite columns use `snake_case`. JSON responses use `camelCase`, for example:

```text
iso2_code           → countryCode
observation_year    → year
fetched_at          → fetchedAt
countries_loaded    → countriesLoaded
```

This keeps SQL idiomatic while providing a stable web-API contract.
