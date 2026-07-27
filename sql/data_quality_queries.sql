-- name: duplicate_country_codes
SELECT COUNT(*) AS violations
FROM (
    SELECT iso2_code
    FROM countries
    GROUP BY iso2_code
    HAVING COUNT(*) > 1
);

-- name: invalid_country_codes
SELECT COUNT(*) AS violations
FROM countries
WHERE length(iso2_code) <> 2
   OR iso2_code <> upper(iso2_code)
   OR iso2_code GLOB '*[^A-Z]*';

-- name: missing_country_names
SELECT COUNT(*) AS violations
FROM countries
WHERE country_name IS NULL
   OR length(trim(country_name)) = 0;

-- name: invalid_coordinates
SELECT COUNT(*) AS violations
FROM countries
WHERE (longitude IS NOT NULL AND (longitude < -180 OR longitude > 180))
   OR (latitude IS NOT NULL AND (latitude < -90 OR latitude > 90));

-- name: duplicate_population_observations
SELECT COUNT(*) AS violations
FROM (
    SELECT iso2_code, observation_year
    FROM population_observations
    GROUP BY iso2_code, observation_year
    HAVING COUNT(*) > 1
);

-- name: orphan_population_observations
SELECT COUNT(*) AS violations
FROM population_observations AS p
LEFT JOIN countries AS c
  ON c.iso2_code = p.iso2_code
WHERE c.iso2_code IS NULL;

-- name: negative_population_values
SELECT COUNT(*) AS violations
FROM population_observations
WHERE population < 0;

-- name: unexpected_indicator_codes
SELECT COUNT(*) AS violations
FROM population_observations
WHERE indicator_code <> 'SP.POP.TOTL';

-- name: countries_without_population
SELECT COUNT(*) AS violations
FROM countries AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM population_observations AS p
    WHERE p.iso2_code = c.iso2_code
);

-- name: incomplete_ingestion_runs
SELECT COUNT(*) AS violations
FROM ingestion_runs
WHERE status = 'running';
