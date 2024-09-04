import geopandas as gpd

from definitions import DATA_PATH

towns = gpd.read_file(DATA_PATH / "shapefiles" / "towns.shp")
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

towns.to_file(DATA_PATH / "shapefiles" / "towns_v2.shp")
