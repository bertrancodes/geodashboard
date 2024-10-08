import cdsapi

from definitions import DATA_PATH

# NOTE: this API will be obsolete by end of September
c = cdsapi.Client()

for year in range(1950, 2025):
    for month in range(1, 13):
        c.retrieve(
            "reanalysis-era5-land",
            {
                "variable": [
                    "2m_temperature",
                    "leaf_area_index_high_vegetation",
                    "leaf_area_index_low_vegetation",
                    "total_precipitation",
                ],
                "year": str(year),
                "month": str(month).zfill(2),
                "day": [
                    "01",
                    "02",
                    "03",
                    "04",
                    "05",
                    "06",
                    "07",
                    "08",
                    "09",
                    "10",
                    "11",
                    "12",
                    "13",
                    "14",
                    "15",
                    "16",
                    "17",
                    "18",
                    "19",
                    "20",
                    "21",
                    "22",
                    "23",
                    "24",
                    "25",
                    "26",
                    "27",
                    "28",
                    "29",
                    "30",
                    "31",
                ],
                "time": [
                    "00:00",
                    "01:00",
                    "02:00",
                    "03:00",
                    "04:00",
                    "05:00",
                    "06:00",
                    "07:00",
                    "08:00",
                    "09:00",
                    "10:00",
                    "11:00",
                    "12:00",
                    "13:00",
                    "14:00",
                    "15:00",
                    "16:00",
                    "17:00",
                    "18:00",
                    "19:00",
                    "20:00",
                    "21:00",
                    "22:00",
                    "23:00",
                ],
                "area": [
                    44,
                    -10,
                    35,
                    5,
                ],
                "format": "netcdf.zip",
            },
            str(
                DATA_PATH
                / "ERA5-Land (zip)"
                / f"era5_land_{year}_{str(month).zfill(2)}.netcdf.zip"
            ),
        )
