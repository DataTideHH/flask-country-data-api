# Data Quality Notes

The service separates source retrieval from API delivery:

```text
World Bank API or versioned fixture
→ source-shape validation
→ normalization
→ transactional SQLite persistence
→ Flask read API
```

The deterministic core enforces these rules:

- country codes must be two uppercase letters
- duplicate requested codes are removed while preserving order
- one country record must match each requested code
- World Bank aggregates are rejected as countries
- coordinates must fall inside valid geographic ranges
- population values may be missing but cannot be negative
- population observations use indicator `SP.POP.TOTL`
- foreign keys prevent observations without countries
- one population value is stored per country and year
- each ingestion run records success or failure

Versioned fixtures are used for tests and CI. Live World Bank calls are available only through the explicit refresh command and are never required for automated tests.
