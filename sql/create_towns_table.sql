CREATE TABLE IF NOT EXISTS towns (
    town_id SERIAL PRIMARY KEY,
    town_name VARCHAR(100) NOT NULL,
    province VARCHAR(100),
    region VARCHAR(100),
    geometry GEOMETRY(MultiPolygon, 4326) NOT NULL
);