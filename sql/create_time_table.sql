CREATE TABLE IF NOT EXISTS time (
    time_id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    year INT GENERATED ALWAYS AS (
        EXTRACT(
            YEAR
            FROM date
        )
    ) STORED,
    month INT GENERATED ALWAYS AS (
        EXTRACT(
            MONTH
            FROM date
        )
    ) STORED,
    day INT GENERATED ALWAYS AS (
        EXTRACT(
            DAY
            FROM date
        )
    ) STORED
);