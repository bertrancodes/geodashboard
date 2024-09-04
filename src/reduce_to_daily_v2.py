import logging
from multiprocessing import Pool
from pathlib import Path

import pandas as pd
import rioxarray
import xarray as xr

from definitions import DATA_PATH, LOG_PATH

logging.basicConfig(
    format="%(processName)s - %(asctime)s - [%(levelname)s]: %(message)s",
    level=logging.INFO,
    filename=LOG_PATH
    / (
        Path(__file__).stem
        + "_"
        + pd.Timestamp.now().strftime("%Y%m%dT%H%M%S")
        + ".log"
    ),
    filemode="w",
)


def hourly_to_daily(hourly_dataset: xr.Dataset) -> xr.Dataset:
    # Daily sum for 'total precipitation'
    logging.debug("Agregating daily data...")
    ds_daily_tp = hourly_dataset["tp"].resample(time="1D").sum()

    # Daily mean for 't2m', 'lai_hv', and 'lai_lv'. Additional min and max
    # for 't2m'
    ds_daily_t2m = hourly_dataset["t2m"].resample(time="1D").mean()
    ds_daily_t2m_min = hourly_dataset["t2m"].resample(time="1D").min()
    ds_daily_t2m_max = hourly_dataset["t2m"].resample(time="1D").max()
    ds_daily_lai_hv = hourly_dataset["lai_hv"].resample(time="1D").mean()
    ds_daily_lai_lv = hourly_dataset["lai_lv"].resample(time="1D").mean()

    logging.debug("Aggregating daily data -> Done")

    daily_dataset = xr.Dataset(
        data_vars={
            "tp": ds_daily_tp,
            "t2m": ds_daily_t2m,
            "t2m_min": ds_daily_t2m_min,
            "t2m_max": ds_daily_t2m_max,
            "lai_hv": ds_daily_lai_hv,
            "lai_lv": ds_daily_lai_lv,
        }
    )

    logging.debug("Writing geospatial metadata...")

    daily_dataset.rio.write_crs("EPSG:4326", inplace=True)
    daily_dataset = daily_dataset.rio.set_spatial_dims(
        x_dim="longitude", y_dim="latitude", inplace=True
    )
    daily_dataset = daily_dataset.rio.write_transform(hourly_dataset.rio.transform())

    logging.debug("Writing geospatial metadata -> Done")

    return daily_dataset


def add_temp_vars_vect(
    hourly_dataset: xr.Dataset,
    daily_dataset: xr.Dataset,
    sunrise_sunset_dataset: xr.Dataset,
) -> xr.Dataset:
    # Initialize new variables in daily_dataset with NaNs
    logging.debug("Intializing variables...")
    daily_dataset["diurnal_temp_variation"] = xr.full_like(
        daily_dataset["t2m"], fill_value=float("nan")
    )
    daily_dataset["max_nocturnal_temp"] = xr.full_like(
        daily_dataset["t2m"], fill_value=float("nan")
    )
    daily_dataset["min_diurnal_temp"] = xr.full_like(
        daily_dataset["t2m"], fill_value=float("nan")
    )

    # Precompute sunrise and sunset times for the whole year
    sunrise_times = sunrise_sunset_dataset["sunrise"]
    sunset_times = sunrise_sunset_dataset["sunset"]

    logging.debug("Intializing variables -> Done")

    for i in range(len(daily_dataset["time"])):
        day = daily_dataset["time"].isel(time=i)
        is_leap_year = pd.to_datetime(day.values).is_leap_year
        doy = day.dt.dayofyear.item()

        logging.debug(f"Leap year = {is_leap_year}")
        if not is_leap_year and doy >= 60:  # Skip 29th Feburary for non leap years
            logging.debug("Skipping February 29th")
            doy = doy + 1

        logging.debug(f"Processing day {day.dt.date.item()}...")

        # Extract sunrise and sunset times for the day
        sunrise_day = sunrise_times.sel(time=doy)
        sunset_day = sunset_times.sel(time=doy)

        # Vectorized computation across lat/lon dimensions
        sunrise_times_vectorized = xr.apply_ufunc(
            lambda time, sunrise: pd.Timestamp(
                year=pd.to_datetime(time).year,
                month=pd.to_datetime(sunrise).month,
                day=pd.to_datetime(sunrise).day,
                hour=pd.to_datetime(sunrise).hour,
                minute=pd.to_datetime(sunrise).minute,
            ),
            day,
            sunrise_day,
            vectorize=True,
        )

        sunset_times_vectorized = xr.apply_ufunc(
            lambda time, sunset: pd.Timestamp(
                year=pd.to_datetime(time).year,
                month=pd.to_datetime(sunset).month,
                day=pd.to_datetime(sunset).day,
                hour=pd.to_datetime(sunset).hour,
                minute=pd.to_datetime(sunset).minute,
            ),
            day,
            sunset_day,
            vectorize=True,
        )

        temp_pixel_day = hourly_dataset["t2m"].sel(
            time=slice(
                f"{day.dt.year.item()}-{day.dt.month.item()}-{day.dt.day.item()}T00:00",
                f"{day.dt.year.item()}-{day.dt.month.item()}-{day.dt.day.item()}T23:59",
            )
        )

        diurnal_period = temp_pixel_day.where(
            (temp_pixel_day.time >= sunrise_times_vectorized).values
            & (temp_pixel_day.time <= sunset_times_vectorized).values,
        )
        nocturnal_period = xr.concat(
            [
                temp_pixel_day.where(
                    (temp_pixel_day.time < sunrise_times_vectorized).values
                ),
                temp_pixel_day.where(
                    (temp_pixel_day.time > sunset_times_vectorized).values
                ),
            ],
            dim="time",
        )

        # Perform computations
        daily_dataset["diurnal_temp_variation"][i] = diurnal_period.max(
            dim="time"
        ) - diurnal_period.min(dim="time")
        daily_dataset["min_diurnal_temp"][i] = diurnal_period.min(dim="time")
        daily_dataset["max_nocturnal_temp"][i] = nocturnal_period.max(dim="time")

        logging.debug(f"Processing day {day} -> Done")

    return daily_dataset


def process_file(
    hourly_file: str | Path, sunrise_sunset_file: str | Path, out_dir: Path
) -> None:
    out_file = out_dir / (hourly_file.stem + "_DA.nc")

    if out_file.exists():
        logging.info(f"{out_file.name} already created. Skipping file.")
    else:
        logging.info(f"Processing {out_file.name}...")
        daily_dataset = main(
            hourly_file=hourly_file, sunrise_sunset_file=sunrise_sunset_file
        )
        daily_dataset.to_netcdf(out_file)
        logging.info(f"Processing {out_file.name} -> Done")


def main(hourly_file: str | Path, sunrise_sunset_file: str | Path) -> xr.Dataset:
    hourly_dataset = xr.open_dataset(hourly_file)
    sunrise_sunset_dataset = xr.open_dataset(sunrise_sunset_file)

    daily_dataset = hourly_to_daily(hourly_dataset=hourly_dataset)

    daily_dataset = add_temp_vars_vect(
        hourly_dataset=hourly_dataset,
        daily_dataset=daily_dataset,
        sunrise_sunset_dataset=sunrise_sunset_dataset,
    )

    hourly_dataset.close()
    sunrise_sunset_dataset.close()

    return daily_dataset


if __name__ == "__main__":
    hourly_files = sorted((DATA_PATH / "ERA5-Land").glob("*.nc"))

    sunrise_sunset_file = DATA_PATH / "sunrise_sunset_v5.nc"

    out_dir = DATA_PATH / "ERA5D-Land"
    out_dir.mkdir(exist_ok=True)

    # Prepare the arguments as a list of tuples
    args = [(hourly_file, sunrise_sunset_file, out_dir) for hourly_file in hourly_files]

    # Use multiprocessing to process files in parallel with starmap
    with Pool() as pool:
        pool.starmap(process_file, args)
