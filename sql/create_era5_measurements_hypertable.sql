SELECT create_hypertable(
        'era5_measurements',
        'time_id',
        if_not_exists => TRUE
    );