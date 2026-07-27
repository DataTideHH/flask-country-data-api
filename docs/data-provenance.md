# Data Provenance

## Source boundary

The live ingestion client reads:

- World Bank country metadata
- World Bank indicator `SP.POP.TOTL` for annual total population

The application does not treat the external response as application-ready data. Each source record passes through validation and normalization before persistence.

## Field lineage

| API field | SQLite field | Source / derivation |
|---|---|---|
| `countryCode` | `countries.iso2_code` | World Bank `iso2Code`, normalized to uppercase and checked against the requested code |
| `countryName` | `countries.country_name` | World Bank `name` |
| `region` | `countries.region_name` | World Bank `region.value`; aggregate records are rejected |
| `incomeLevel` | `countries.income_level` | World Bank `incomeLevel.value` |
| `capitalCity` | `countries.capital_city` | World Bank `capitalCity` |
| `coordinates.longitude` | `countries.longitude` | World Bank `longitude`, converted to numeric and range-checked |
| `coordinates.latitude` | `countries.latitude` | World Bank `latitude`, converted to numeric and range-checked |
| `latestPopulation.year` | `population_observations.observation_year` | Maximum stored observation year for the country |
| `latestPopulation.value` | `population_observations.population` | World Bank `SP.POP.TOTL` value; missing source values remain `NULL` |
| `provenance.source` | `source_name` | Client label: live API or fixture snapshot |
| `provenance.fetchedAt` | `fetched_at` | UTC timestamp assigned at refresh start |

## Live and fixture modes

### Live mode

The refresh CLI calls the World Bank API explicitly. The stored source label is `World Bank API`.

### Fixture mode

Version-controlled JSON fixtures preserve a representative World Bank response shape for tests, demonstrations and CI. The stored source label is `World Bank fixture snapshot`.

Fixture values are not presented as a continuously current dataset. Their purpose is deterministic validation of mapping, persistence, quality checks and API behavior.

## Temporal semantics

Two different times are retained:

- `observation_year` describes when the population measurement applies.
- `fetched_at` describes when this application retrieved or loaded the record.

The API must not imply that retrieval time is the observation time.

## Refresh and replacement behavior

For each requested country and year range:

1. source data is retrieved and validated in memory
2. country records are inserted or updated
3. existing population rows inside the requested range are deleted
4. validated source observations are inserted
5. the transaction commits
6. the ingestion run is marked successful

If validation or persistence fails, the data transaction rolls back and the run is marked failed. Previously committed data remains available to read clients.

## Quality and authority statement

The service preserves source attribution and validates structure, identity, ranges and relational integrity. It does not independently certify the statistical methodology or publication process of the upstream source.
