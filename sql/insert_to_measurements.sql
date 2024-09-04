INSERT INTO measurements(
        town_id,
        time_id,
        t2m,
        tp,
        t2m_min,
        t2m_max,
        max_nocturnal_temp,
        min_diurnal_temp,
        diurnal_temp_variation
    )
VALUES (
        :town_id,
        :time_id,
        :t2m,
        :tp,
        :t2m_min,
        :t2m_max,
        :max_nocturnal_temp,
        :min_diurnal_temp,
        :diurnal_temp_variation
    );