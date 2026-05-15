CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_key TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    category TEXT NOT NULL,
    connector_type TEXT NOT NULL,
    source_url TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_key TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    rows_read INTEGER DEFAULT 0,
    rows_written INTEGER DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS regional_observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_key TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    dataset_category TEXT NOT NULL,
    observation_type TEXT,
    observed_at TIMESTAMPTZ,
    year INTEGER,
    state TEXT DEFAULT 'OR',
    county TEXT,
    city TEXT,
    zip_code TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    geometry GEOMETRY(Point, 4326),
    metric_name TEXT,
    metric_value DOUBLE PRECISION,
    unit TEXT,
    confidence_level TEXT,
    raw_properties_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_regional_observations_source_key ON regional_observations(source_key);
CREATE INDEX IF NOT EXISTS idx_regional_observations_year ON regional_observations(year);
CREATE INDEX IF NOT EXISTS idx_regional_observations_geom ON regional_observations USING GIST(geometry);
