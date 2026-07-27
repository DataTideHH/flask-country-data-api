---
layout: default
title: Flask Country Data API
description: Reproducible World Bank ingestion, SQLite persistence, SQL data-quality checks and a documented Flask read API.
---

# Flask Country Data API

A compact data-integration project that turns external World Bank country metadata and population observations into a controlled, explainable SQLite-backed API.

The project is designed as evidence for Data/BI, process-analysis and Python/API work rather than as a generic backend showcase.

## Controlled data workflow

```text
World Bank API or versioned fixtures
→ source validation
→ normalization
→ transactional SQLite persistence
→ SQL data-quality checks
→ versioned Flask read API
```

Normal API requests read the last successfully committed local database state. External retrieval happens only through an explicit refresh command, so source availability is separated from data delivery.

## Portfolio evidence

| Area | What the repository demonstrates |
|---|---|
| Data integration | Explicit source retrieval, timeout handling and deterministic fixtures |
| Data modelling | Country master data, annual population observations and ingestion history |
| Data quality | Ten named SQL checks with error and warning severity |
| Process observability | Successful and failed refresh runs with timestamps and row counts |
| API design | Versioned endpoints, bounded parameters and stable JSON errors |
| Documentation | Architecture, ERD, data dictionary, provenance and OpenAPI 3.1 |
| Reproducibility | Python 3.12 CI on Ubuntu and Windows without live network calls |

## API surface

| Endpoint | Purpose |
|---|---|
| `GET /health` | Database availability and basic counts |
| `GET /api/v1/countries` | Filtered country list |
| `GET /api/v1/countries/<code>` | Country details and latest population |
| `GET /api/v1/countries/<code>/population` | Population history for a selected period |
| `GET /api/v1/summary` | Dataset-level metrics |
| `GET /api/v1/data-quality` | SQL data-quality report |
| `GET /api/v1/ingestion-runs` | Recent refresh execution history |

The machine-readable contract is maintained in [`openapi/openapi.yaml`](https://github.com/DataTideHH/flask-country-data-api/blob/main/openapi/openapi.yaml).

## Documentation

- [Architecture and component responsibilities](architecture.md)
- [Relational data model](data-model.md)
- [Data dictionary](data-dictionary.md)
- [Data provenance](data-provenance.md)
- [Data-quality rules and status logic](data-quality-notes.md)
- [SQLite schema](https://github.com/DataTideHH/flask-country-data-api/blob/main/sql/schema.sql)
- [Version-controlled SQL quality checks](https://github.com/DataTideHH/flask-country-data-api/blob/main/sql/data_quality_queries.sql)

## Scope boundary

This is intentionally a small, understandable project. It does not add an unrelated frontend, authentication system, container platform or cloud deployment. The value lies in the controlled path from external data to validated persistence, observable processing and a documented read contract.

## Connected portfolio projects

- [Music Production Data Lab](https://datatidehh.github.io/music-production-data-lab/) — relational modelling, SQL reporting views, data quality and a documented Power BI semantic model
- [Network Operations Data Lab](https://datatidehh.github.io/network-operations-data-lab/) — Python, SQL and BI-oriented reporting over sanitized infrastructure records
- [Spring Boot Process API Basics](https://datatidehh.github.io/spring-boot-process-api-basics/) — supporting Java REST API progression
- [DataTideHH portfolio overview](https://datatidehh.github.io/DataTideHH/)

## Repository

Source code, tests and complete setup instructions: [github.com/DataTideHH/flask-country-data-api](https://github.com/DataTideHH/flask-country-data-api)
