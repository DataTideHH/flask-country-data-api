# Data Quality

The service separates source retrieval from API delivery:

```text
World Bank API or versioned fixture
→ source-shape validation
→ normalization
→ transactional SQLite persistence
→ SQL data-quality checks
→ Flask read API
```

## Quality layers

### 1. Request validation

- country codes must contain exactly two letters
- values are normalized to uppercase
- duplicate requested codes are removed while preserving order
- request size and numeric query parameters are bounded

### 2. Source validation

- the returned country must match the requested code
- World Bank aggregate records are rejected as countries
- names and nested source structures must have the expected shape
- coordinates must fall inside valid geographic ranges
- population rows must use indicator `SP.POP.TOTL`
- observation years must be plausible
- missing population values remain `NULL`; negative values are rejected

### 3. Relational constraints

- country codes are primary keys
- one population row is allowed per country and year
- population rows require an existing country
- population and coordinate ranges are constrained in SQLite
- ingestion status values are controlled

### 4. Version-controlled SQL checks

The application executes the named queries in [`sql/data_quality_queries.sql`](../sql/data_quality_queries.sql).

| Check | Severity | Purpose |
|---|---|---|
| `duplicate_country_codes` | Error | Detect duplicate country keys |
| `invalid_country_codes` | Error | Detect malformed stored codes |
| `missing_country_names` | Error | Detect empty required names |
| `invalid_coordinates` | Error | Detect out-of-range coordinates |
| `duplicate_population_observations` | Error | Detect duplicate country/year rows |
| `orphan_population_observations` | Error | Detect broken country references |
| `negative_population_values` | Error | Detect invalid negative measures |
| `unexpected_indicator_codes` | Error | Detect non-population indicators |
| `countries_without_population` | Warning | Identify countries without observations |
| `incomplete_ingestion_runs` | Warning | Identify runs left in `running` state |

The `/api/v1/data-quality` endpoint returns each check, its severity, violation count and pass/fail state. The overall status is:

- `passed` when no violations exist
- `warning` when only warning checks have violations
- `failed` when at least one error check has violations

## Process observability

Every refresh invocation creates an `ingestion_runs` row before source access begins. The run is then completed as `success` or `failed`, preserving counts, timestamps and a bounded error message.

This makes a failed refresh visible without overwriting the last committed dataset.

## Deterministic validation

Versioned fixtures are used for tests and CI. Live World Bank calls are available only through the explicit refresh command and are never required for automated tests.

CI verifies:

- Python compilation
- unit, persistence, route and OpenAPI tests
- deterministic fixture ingestion
- a persisted `passed` data-quality report
- identical behavior on Python 3.12 for Ubuntu and Windows
