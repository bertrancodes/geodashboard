CREATE TABLE IF NOT EXISTS modis_measurements (
    measurement_id SERIAL,
    town_id INT REFERENCES towns(town_id),
    time_id INT REFERENCES time(time_id),
    ndvi FLOAT
);