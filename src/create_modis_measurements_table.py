from pathlib import Path

import geopandas as gpd
import rioxarray
import xarray as xr
from shapely import box
from sqlalchemy import create_engine, text
from tqdm import tqdm

from definitions import DATA_PATH, DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
from utils import read_sql_query


def mask_bad_pixels(qa_bits: int) -> bool:
    """
    Given the MODIS VI QA value, return False if pixel is ok and True if pixel
    should be masked. See: https://lpdaac.usgs.gov/documents/103/MOD13_User_Guide_V6.pdf
    table 5, page 16.
    """
    # Extract bits for each relevant category.
    vi_quality = qa_bits & 0b11  # Bits 0-1
    vi_usefulness = (qa_bits >> 2) & 0b1111  # Bits 2-5
    aerosol_quantity = (qa_bits >> 6) & 0b11  # Bits 6-7
    adjacent_cloud = (qa_bits >> 8) & 0b1  # Bit 8
    mixed_clouds = (qa_bits >> 10) & 0b1  # Bit 10
    snow_ice = (qa_bits >> 14) & 0b1  # Bit 14
    shadow = (qa_bits >> 15) & 0b1  # Bit 15

    # Mask conditions
    if vi_quality in [0b10, 0b11]:  # Cloudy or not produced
        return True
    if vi_usefulness >= 0b1100:  # Low quality or not useful
        return True
    if aerosol_quantity == 0b11:  # High aerosol quantity
        return True
    if adjacent_cloud == 1:  # Adjacent cloud detected
        return True
    if mixed_clouds == 1:  # Mixed clouds detected
        return True
    if snow_ice == 1:  # Snow/ice detected
        return True
    if shadow == 1:  # Shadow detected
        return True

    # If no conditions met, pixel is good
    return False


def create_table() -> None:
    """
    Connect to the database, create the 'modis_measurements' table and hypertable
    """
    # Connection URL
    engine = create_engine(
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    connection = engine.connect()

    # We need to drop the primary key from measurement_id and
    # the UNIQUE constraint in order to create the timescale hypertable
    create_measurements_table = read_sql_query("create_modis_measurements_table.sql")
    connection.execute(text(create_measurements_table))
    connection.commit()

    create_measurements_hypertable = read_sql_query(
        "create_modis_measurements_hypertable.sql"
    )
    connection.execute(text(create_measurements_hypertable))
    connection.commit()
    connection.close()


def insert_data(modis_file: str | Path) -> None:
    """
    Connect to the database and insert measurements data into it
    """

    engine = create_engine(
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    connection = engine.connect()

    towns = gpd.read_parquet(DATA_PATH / "shapefiles" / "towns_v2.parquet")
    towns = towns.to_crs(epsg=4326)

    modis_ds = xr.open_dataset(modis_file)
    modis_ds = modis_ds.convert_calendar(calendar="gregorian")
    date = modis_ds.indexes["time"].strftime("%Y-%m-%d")[0]

    df = modis_ds.to_dataframe().reset_index()
    modis_ds.close()

    df.dropna(inplace=True)
    df = df.reset_index()
    df["_250m_16_days_VI_Quality"] = df["_250m_16_days_VI_Quality"].astype(int)
    df["_250m_16_days_VI_Quality"] = df["_250m_16_days_VI_Quality"].apply(
        mask_bad_pixels
    )

    # Regenerate pixel polygons from pixel centroids
    offset_value = 0.002083333333 / 2
    xmin = df["lon"] - offset_value
    xmax = df["lon"] + offset_value
    ymin = df["lat"] - offset_value
    ymax = df["lat"] + offset_value
    polygons = box(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax)

    gdf = gpd.GeoDataFrame(
        df,
        geometry=polygons,
    )
    del df
    gdf = gdf[~gdf["_250m_16_days_VI_Quality"]]

    # So the thing is that by doing this with predicate None, we are performing the
    # spatial join with the bboxes of the objetcs, rather than with the objetcs
    # themselves. Given that results are almost the same (delta ~ 0.0001), we use
    # this method since it is WAY FASTER than using 'intersect' as predicate.
    # See: https://github.com/geopandas/geopandas/discussions/3063
    joined_gdf = gpd.sjoin(gdf, towns, how="inner", predicate=None)
    del gdf
    joined_gdf = joined_gdf.drop(
        columns=[
            "lon",
            "lat",
            "geometry",
            "index_right",
            "_250m_16_days_VI_Quality",
            "crs",
            "time",
            "index",
        ]
    )

    joined_gdf = joined_gdf.groupby(["town_name"]).mean(numeric_only=True)

    for col in joined_gdf:
        joined_gdf[col] = joined_gdf[col].apply(lambda x: round(x, 2))

    joined_gdf = joined_gdf.rename(columns={"_250m_16_days_NDVI": "ndvi"})
    # Define queries to get town_id and time_id
    town_query = read_sql_query("select_towns.sql")
    time_query = read_sql_query("select_date.sql")
    date_dict = {"date": date}

    result_town = connection.execute(text(town_query)).mappings().all()
    result_times = connection.execute(text(time_query), date_dict).mappings().all()

    # Convert result_town into a dictionary: {'town_name': town_id}
    town_dict = {row["town_name"]: row["town_id"] for row in result_town}

    # Add town_id and time_id from the database to the joined_gdf
    # to efficiently insert into the 'modis_measurements' table
    joined_gdf["town_id"] = joined_gdf.index.get_level_values("town_name").map(
        town_dict
    )
    joined_gdf["time_id"] = result_times[0]["time_id"]

    values = joined_gdf.to_dict(orient="records")

    insert_to_measurements = read_sql_query("insert_to_modis_measurements.sql")

    connection.execute(text(insert_to_measurements), values)
    connection.commit()

    connection.close()


def create_index() -> None:
    """
    Connect to the database and create an index for town_id in 'modis_measurements' table
    """
    engine = create_engine(
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    connection = engine.connect()
    create_town_id_index = read_sql_query("create_town_id_index_modis.sql")
    connection.execute(text(create_town_id_index))
    connection.commit()
    connection.close()


if __name__ == "__main__":
    create_table()
    files = sorted((DATA_PATH / "modis_ndvi").glob("*.nc"))

    # NOTE: we cannot use multiprocessing since we do not have enough RAM
    for file in tqdm(files, desc="Inserting MODIS NDVI data to PostgreSQL"):
        insert_data(modis_file=file)

    create_index()
