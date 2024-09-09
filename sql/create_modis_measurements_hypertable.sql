SELECT create_hypertable(
        'modis_measurements',
        'time_id',
        if_not_exists => TRUE
    );