CREATE TABLE IF NOT EXISTS countries (
    iso2_code TEXT PRIMARY KEY
        CHECK (length(iso2_code) = 2 AND iso2_code = upper(iso2_code)),
    country_name TEXT NOT NULL CHECK (length(trim(country_name)) > 0),
    region_name TEXT,
    income_level TEXT,
    capital_city TEXT,
    longitude REAL CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180),
    latitude REAL CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),
    source_name TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS population_observations (
    iso2_code TEXT NOT NULL,
    observation_year INTEGER NOT NULL CHECK (observation_year >= 1960),
    population INTEGER CHECK (population IS NULL OR population >= 0),
    indicator_code TEXT NOT NULL CHECK (indicator_code = 'SP.POP.TOTL'),
    source_name TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (iso2_code, observation_year),
    FOREIGN KEY (iso2_code)
        REFERENCES countries (iso2_code)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('running', 'success', 'failed')),
    countries_requested INTEGER NOT NULL CHECK (countries_requested >= 0),
    countries_loaded INTEGER NOT NULL DEFAULT 0 CHECK (countries_loaded >= 0),
    observations_loaded INTEGER NOT NULL DEFAULT 0 CHECK (observations_loaded >= 0),
    rejected_records INTEGER NOT NULL DEFAULT 0 CHECK (rejected_records >= 0),
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_population_year
    ON population_observations (observation_year);

CREATE INDEX IF NOT EXISTS idx_countries_region
    ON countries (region_name);
