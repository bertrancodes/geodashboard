import geopandas as gpd
import pandas as pd
import plotly.express as px
from shapely import from_wkb
from sqlalchemy import create_engine, text

from definitions import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
from utils import read_sql_query

variables = {
    "Total precipitation (mm)": "tp",
    "Mean temperature 2m (K)": "t2m",
    "Minimum temperature 2m (K)": "t2m_min",
    "Maximum temperature 2m (K)": "t2m_max",
    "Maximum nocturnal temperature (K)": "max_nocturnal_temp",
    "Minimum diurnal temperature (K)": "min_diurnal_temp",
    "Diurnal temperature variation (K)": "diurnal_temp_variation",
    "NDVI": "ndvi",
}

engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


def fetch_available_ndvi_dates():
    fetch_statement = read_sql_query("fetch_ndvi_dates.sql")
    ndvi_dates = pd.read_sql(sql=text(fetch_statement), con=engine)
    return pd.to_datetime(ndvi_dates["date"]).sort_values()


def blank_figure():
    fig = px.scatter()
    fig.update_layout(template=None)
    fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False)
    fig.update_yaxes(showgrid=False, showticklabels=False, zeroline=False)
    return fig


def query_measurements(variable, date):
    allowed_variables = {
        "tp": "select_tp.sql",
        "t2m": "select_t2m.sql",
        "t2m_min": "select_t2m_min.sql",
        "t2m_max": "select_t2m_max.sql",
        "max_nocturnal_temp": "select_max_nocturnal_temp.sql",
        "min_diurnal_temp": "select_min_diurnal_temp.sql",
        "diurnal_temp_variation": "select_diurnal_temp_variation.sql",
        "ndvi": "select_ndvi.sql",
    }

    if variable not in allowed_variables:
        raise ValueError("Invalid variable")

    select_measurements = read_sql_query(allowed_variables[variable])
    df = pd.read_sql(sql=text(select_measurements), con=engine, params={"date": date})
    df["geometry"] = from_wkb(df["geometry"])
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    gdf["geometry"] = gdf.simplify(tolerance=0.0005, preserve_topology=False)
    gdf = gdf.set_index("town_name")
    return gdf
