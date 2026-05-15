CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS regional_observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    source_name TEXT NOT NULL,
    source_url TEXT,
    dataset_category TEXT NOT NULL,
    observation_type TEXT,

    observed_at TIMESTAMPTZ,
    year INTEGER,

    state TEXT DEFAULT 'Oregon',
    county TEXT,
    city TEXT,
    zip_code TEXT,

    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    geometry GEOMETRY(GEOMETRY, 4326),

    metric_name TEXT,
    metric_value DOUBLE PRECISION,
    unit TEXT,

    confidence_level TEXT,
    raw_properties_json JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_regional_observations_geom
ON regional_observations
USING GIST (geometry);

CREATE INDEX IF NOT EXISTS idx_regional_observations_category
ON regional_observations(dataset_category);

CREATE INDEX IF NOT EXISTS idx_regional_observations_year
ON regional_observations(year);