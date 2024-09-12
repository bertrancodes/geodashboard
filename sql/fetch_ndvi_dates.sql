SELECT DISTINCT ti.date
FROM modis_measurements mm
    JOIN time ti ON mm.time_id = ti.time_id
ORDER BY ti.date ASC;