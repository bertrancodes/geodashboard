SELECT time_id,
    date
FROM time
WHERE date BETWEEN :start_date and :end_date;