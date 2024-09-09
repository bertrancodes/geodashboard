INSERT INTO modis_measurements(
        town_id,
        time_id,
        ndvi
    )
VALUES (
        :town_id,
        :time_id,
        :ndvi
    );