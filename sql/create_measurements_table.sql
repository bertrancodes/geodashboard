CREATE TABLE IF NOT EXISTS measurements (
    measurement_id SERIAL,
    town_id INT REFERENCES towns(town_id),
    time_id INT REFERENCES time(time_id),
    t2m FLOAT,
    tp FLOAT,
    ndvi FLOAT,
    t2m_min FLOAT,
    t2m_max FLOAT,
    max_nocturnal_temp FLOAT,
    min_diurnal_temp FLOAT,
    diurnal_temp_variation FLOAT
);