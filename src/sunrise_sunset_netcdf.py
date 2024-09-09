from multiprocessing import Pool

import numpy as np
import pandas as pd
import rioxarray
import xarray as xr
from affine import Affine
from astral import LocationInfo
from astral.sun import sun

from definitions import DATA_PATH


def calculate_sun_times(latitude: float, longitude: float, date: str) -> list[str, str]:
    """Calculate sunrise and sunset for a given latitude, longitude, and date"""

    city = LocationInfo(
        timezone="Europe/London", latitude=latitude, longitude=longitude
    )

    s = sun(city.observer, date=date)

    return s["sunrise"], s["sunset"]


def main(
    lon_west: float,
    lon_east: float,
    lat_north: float,
    lat_south: float,
    nrows: int,
    ncols: int,
    start_date: str,
    end_date: str,
) -> xr.Dataset:
    """Create an xarrat.Dataset with EPSG:4326 containing the sunrise and sunset
    hours for each pixel across all the days for the year 2020. We arbitrary use
    2020 as is a leap year and thus it has all possible DOYs that a year may have"""
    lats = np.linspace(lat_north, lat_south, nrows)
    lons = np.linspace(lon_west, lon_east, ncols)
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    time = np.arange(1, 366 + 1, 1)

    # Prepare inputs for parallel processing
    input_args = [(lat, lon, date) for date in dates for lat in lats for lon in lons]

    # Parallel processing using starmap
    with Pool() as pool:
        results = pool.starmap(calculate_sun_times, input_args)

    # Reshape results back into shape (time, lat, lon)
    sunrise = (
        np.array([r[0] for r in results])
        .reshape((len(dates), nrows, ncols))
        .astype(np.datetime64)
    )
    sunset = (
        np.array([r[1] for r in results])
        .reshape((len(dates), nrows, ncols))
        .astype(np.datetime64)
    )

    ds = xr.Dataset(
        data_vars={
            "sunrise": (
                ["time", "latitude", "longitude"],
                sunrise,
            ),
            "sunset": (["time", "latitude", "longitude"], sunset),
        },
        coords={
            "time": time,
            "latitude": lats,
            "longitude": lons,
        },
    )

    # Add xarray.Dataset metadata
    ds.coords["time"].attrs["description"] = (
        "Day of year, ranging from 1 to 365 (or 366 for leap years)"
    )
    sunset_sunrise_units = "hours since 2020-01-01T00:00:00"
    ds.sunrise.encoding["units"] = sunset_sunrise_units
    ds.sunset.encoding["units"] = sunset_sunrise_units
    ds.rio.write_crs("EPSG:4326", inplace=True)
    transform = Affine.translation(lon_west - 0.05, lat_north + 0.05) * Affine.scale(
        0.1, -0.1
    )
    # Set the affine transform
    ds = ds.rio.set_spatial_dims(x_dim="longitude", y_dim="latitude", inplace=True)
    ds = ds.rio.write_transform(transform)

    return ds


if __name__ == "__main__":
    lon_west = -10
    lon_east = 5
    lat_north = 44
    lat_south = 35
    nrows = 91
    ncols = 151
    start_date = "2020-01-01"
    end_date = "2020-12-31"

    ds = main(
        lon_west=lon_west,
        lon_east=lon_east,
        lat_north=lat_north,
        lat_south=lat_south,
        nrows=nrows,
        ncols=ncols,
        start_date=start_date,
        end_date=end_date,
    )

    netcdf_path = DATA_PATH / "sunrise_sunset_v5.nc"
    ds.to_netcdf(netcdf_path)
