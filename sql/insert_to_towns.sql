INSERT INTO towns (town_name, province, region, geometry)
VALUES (
        :town_name,
        :province,
        :region,
        ST_GeomFromText(:geometry, 4326)
    );