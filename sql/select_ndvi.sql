SELECT t.town_name,
    t.geometry,
    m.ndvi
FROM towns t
    JOIN modis_measurements m ON t.town_id = m.town_id
    JOIN time ti ON m.time_id = ti.time_id
WHERE ti.date = :date