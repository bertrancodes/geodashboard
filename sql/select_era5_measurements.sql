SELECT t.town_name,
    t.geometry,
    m.t2m
FROM towns t
    JOIN era5_measurements m ON t.town_id = m.town_id
    JOIN time ti ON m.time_id = ti.time_id
WHERE ti.date = :date