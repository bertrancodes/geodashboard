from datetime import date

import dash
import geopandas as gpd
import pandas as pd
import plotly.express as px
from dash import Input, Output, callback, dcc, html
from shapely import from_wkb
from sqlalchemy import create_engine, text

from src.definitions import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

bounds = [(35, 5), (45, -10)]
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

external_stylesheets = [
    {
        "href": (
            "https://fonts.googleapis.com/css2?" "family=Lato:wght@400;700&display=swap"
        ),
        "rel": "stylesheet",
    },
]


engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


def blank_figure():
    fig = px.scatter()
    fig.update_layout(template=None)
    fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False)
    fig.update_yaxes(showgrid=False, showticklabels=False, zeroline=False)
    return fig


def query_towns_and_measurements_v2(variable, date):
    # Unpack bounds from the list: [[south_lat, west_lon], [north_lat, east_lon]]
    bounds = [(35, 5), (45, -10)]
    south_lat, west_lon = bounds[0]
    north_lat, east_lon = bounds[1]

    # SQL query with bounding box and date
    query = f"""
        SELECT t.town_name, t.geometry, m.{variable}
        FROM towns t
        JOIN era5_measurements m ON t.town_id = m.town_id
        JOIN time ti ON m.time_id = ti.time_id
        WHERE ti.date = '{date}'
        AND ST_Intersects(t.geometry, ST_MakeEnvelope({west_lon}, {south_lat}, {east_lon}, {north_lat}, 4326));
    """

    df = pd.read_sql(query, engine)
    # Convert WKB to shapely objects
    df["geometry"] = from_wkb(df["geometry"])
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    gdf["geometry"] = gdf.simplify(tolerance=0.0001, preserve_topology=False)
    gdf = gdf.set_index("town_name")
    return gdf


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Geodashboard"
app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.P(children="⛅️", className="header-emoji"),
                html.H1(children="Geodashboard", className="header-title"),
                html.P(
                    children=("Visualize climate variables anomalies in Spain"),
                    className="header-description",
                ),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Variable", className="menu-title"),
                        dcc.Dropdown(
                            id="variable-filter",
                            options=[
                                {"label": label, "value": value}
                                for label, value in variables.items()
                            ],
                            value="t2m",
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(children="Date", className="menu-title"),
                        dcc.DatePickerSingle(
                            id="date-filter",
                            min_date_allowed=date(1950, 1, 1),
                            max_date_allowed=date(2024, 7, 15),
                            initial_visible_month=date(2020, 1, 1),
                            date=date(2020, 1, 1),
                        ),
                    ]
                ),
            ],
            className="menu",
        ),
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="graph",
                        figure=blank_figure(),
                        style={
                            "width": "125vh",
                            "height": "85vh",
                            "marginLeft": "auto",
                            "marginRight": "auto",
                        },
                    ),
                )
            ],
            style={"textAlign": "center"},
        ),
    ]
)


# Add users' capabilities to filter the map by date and varaible
@callback(
    Output(component_id="graph", component_property="figure"),
    [
        Input(component_id="variable-filter", component_property="value"),
        Input(component_id="date-filter", component_property="date"),
    ],
)
def update_graph(variable, date):
    temperatures = [
        "t2m",
        "t2m_min",
        "t2m_max",
        "max_nocturnal_temp",
        "min_diurnal_temp",
        "diurnal_temp_variation",
    ]
    precipitation = "tp"

    if variable in temperatures:
        units = "Temperature (K)"
        cmap = "RdBu_r"
    elif variable == precipitation:
        units = "Total precipitation (mm)"
        cmap = "RdBu"
    else:
        units = "NDVI"

    gdf = query_towns_and_measurements_v2(variable=variable, date=date)
    percentile_5 = gdf[variable].quantile(0.05)
    percentile_95 = gdf[variable].quantile(0.95)
    fig = px.choropleth_map(
        gdf,
        geojson=gdf.geometry,
        locations=gdf.index,
        color=variable,
        color_continuous_scale=cmap,
        range_color=(percentile_5, percentile_95),
        map_style="carto-positron",
        zoom=5.25,
        center={"lat": 40, "lon": -3},
        opacity=0.5,
        labels={variable: units},
    )
    return fig


if __name__ == "__main__":
    app.run(debug=True)
