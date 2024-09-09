from pathlib import Path

import geopandas as gpd

from definitions import DATA_PATH


def main(file: str | Path) -> gpd.GeoDataFrame:
    """
    Parse the geometry file columns' names
    """
    towns = gpd.read_file(file)
    towns = towns.rename(
        columns={
            "NAMEUNIT": "town_name",
            "NAMEUNIT_2": "province",
            "NAMEUNIT_3": "region",
        }
    )

    # Select the regions' proper name
    towns["region"] = towns["region"].apply(lambda x: x.split("/")[-1])
    towns.loc[towns["region"] == "Comunitat Valenciana", "region"] = "País Valencià"
    towns["province"] = towns["province"].apply(lambda x: x.split("/")[0])

    return towns


if __name__ == "__main__":
    file = DATA_PATH / "shapefiles" / "towns.shp"
    towns = main(file=file)
    towns.to_parquet(DATA_PATH / "shapefiles" / "towns_v2.parquet")
