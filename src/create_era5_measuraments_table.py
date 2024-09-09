from multiprocessing import Pool, cpu_count
from pathlib import Path

import geopandas as gpd
import rioxarray
import xarray as xr
from shapely import box
from sqlalchemy import create_engine, text
from tqdm import tqdm

from definitions import DATA_PATH, DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
from utils import read_sql_query


def create_table() -> None:
    """
    Connect to the database, create the 'era5_measurements' table and hypertable
    """

    engine = create_engine(
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    connection = engine.connect()

    # We need to drop the primary key from measurement_id and
    # the UNIQUE constraint in order to create the timescale hypertable
    create_measurements_table = read_sql_query("create_era5_measurements_table.sql")
    connection.execute(text(create_measurements_table))
    connection.commit()

    create_measurements_hypertable = read_sql_query(
        "create_era5_measurements_hypertable.sql"
    )
    connection.execute(text(create_measurements_hypertable))
    connection.commit()
    connection.close()


def insert_data(anomaly_file: str | Path) -> None:
    """
    Connect to the database and insert measurements data into it
    """
    engine = create_engine(
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    connection = engine.connect()

    towns = gpd.read_parquet(DATA_PATH / "shapefiles" / "towns_v2.parquet")
    towns = towns.to_crs(epsg=4326)

    anomaly_ds = xr.open_dataset(anomaly_file)
    start_date = str(anomaly_ds.time.dt.date.min().values)
    end_date = str(anomaly_ds.time.dt.date.max().values)

    df = anomaly_ds.to_dataframe().reset_index()
    anomaly_ds.close()
    df.dropna(inplace=True)
    df = df.reset_index()

    # Regenerate pixel polygons from pixel centroids
    offset_value = 0.05
    xmin = df["longitude"] - offset_value
    xmax = df["longitude"] + offset_value
    ymin = df["latitude"] - offset_value
    ymax = df["latitude"] + offset_value
    polygons = box(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax)

    gdf = gpd.GeoDataFrame(
        df,
        geometry=polygons,
        crs="EPSG:4326",
    )

    gdf["tp"] = gdf["tp"] * 1000  # ERA5 has precipitation in m -> convert to mm

    # So the thing is that by doing this with predicate None, we are performing the
    # spatial join with the bboxes of the objetcs, rather than with the objetcs
    # themselves. Given that results are almost the same (delta ~ 0.0001), we use
    # this method since it is WAY FASTER than using 'intersect' as predicate.
    # See: https://github.com/geopandas/geopandas/discussions/3063
    joined_gdf = gpd.sjoin(gdf, towns, how="inner", predicate=None)
    joined_gdf = joined_gdf.drop(
        columns=[
            "longitude",
            "latitude",
            "spatial_ref",
            "geometry",
            "lai_hv",
            "lai_lv",
            "index_right",
            "index",
        ]
    )

    joined_gdf = joined_gdf.groupby(["time", "town_name"]).mean(numeric_only=True)

    for col in joined_gdf:
        joined_gdf[col] = joined_gdf[col].apply(lambda x: round(x, 2))

    # Define queries to get town_id and time_id
    town_query = read_sql_query("select_towns.sql")
    time_query = read_sql_query("select_dates.sql")
    dates = {"start_date": start_date, "end_date": end_date}

    result_town = connection.execute(text(town_query)).mappings().all()
    result_times = connection.execute(text(time_query), dates).mappings().all()

    # Convert result_town into a dictionary: {'town_name': town_id}
    town_dict = {row["town_name"]: row["town_id"] for row in result_town}

    # Convert result_times into a dictionary: {'date': time_id}
    time_dict = {row["date"]: row["time_id"] for row in result_times}

    # Add town_id and time_id from the database to the joined_gdf
    # to efficiently insert into the 'era6_measurements' table
    joined_gdf["town_id"] = joined_gdf.index.get_level_values("town_name").map(
        town_dict
    )
    joined_gdf["time_id"] = joined_gdf.index.get_level_values("time").map(time_dict)

    values = joined_gdf.to_dict(orient="records")

    insert_to_measurements = read_sql_query("insert_to_era5_measurements.sql")

    connection.execute(text(insert_to_measurements), values)
    connection.commit()

    connection.close()


def create_index() -> None:
    """
    Connect to the database and create an index for town_id in 'era5_measurements' table
    """
    engine = create_engine(
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    connection = engine.connect()
    create_town_id_index = read_sql_query("create_town_id_index_era5.sql")
    connection.execute(text(create_town_id_index))
    connection.commit()
    connection.close()


if __name__ == "__main__":
    create_table()
    files = sorted((DATA_PATH / "anomaly_all").glob("*.nc"))

    with Pool(processes=cpu_count()) as pool, tqdm(total=len(files)) as pbar:
        for result in pool.imap(insert_data, files):
            pbar.update()
            pbar.refresh()

    create_index()
