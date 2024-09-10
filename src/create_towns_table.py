import geopandas as gpd
from sqlalchemy import create_engine, text

from definitions import DATA_PATH, DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
from utils import read_sql_query


def main() -> None:
    """
    Connect to the database, create the 'towns' table and insert data into it
    """
    towns = gpd.read_file(DATA_PATH / "shapefiles" / "towns_v2.parquet")
    towns = towns.to_crs(epsg=4326)
    engine = create_engine(
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    connection = engine.connect()

    create_towns_table = read_sql_query("create_towns_table.sql")

    # Execute the SQL query
    connection.execute(text(create_towns_table))
    connection.commit()

    towns["geometry"] = towns["geometry"].apply(lambda geom: geom.wkt)
    data = towns.to_dict(orient="records")

    # SQL query to insert data
    insert_to_towns = read_sql_query("insert_to_towns.sql")

    connection.execute(text(insert_to_towns), data)
    connection.commit()

    connection.close()


def create_index() -> None:
    """
    Connect to the database, create the 'towns' table and insert data into it
    """
    engine = create_engine(
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    connection = engine.connect()

    create_towns_spatial_idx = read_sql_query("create_towns_spatial_index.sql")

    # Execute the SQL query
    connection.execute(text(create_towns_spatial_idx))
    connection.commit()
    connection.close()


if __name__ == "__main__":
    main()
