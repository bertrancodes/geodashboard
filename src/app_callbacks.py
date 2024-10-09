from datetime import date

import pandas as pd
import plotly.express as px
from dash import Input, Output

from app_data_fetcher import fetch_available_ndvi_dates, query_measurements

ndvi_dates = fetch_available_ndvi_dates()


def register_callbacks(app):
    @app.callback(
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
            lowers = -5
            uppers = 5
        elif variable == precipitation:
            units = "Total precipitation (mm)"
            cmap = "RdBu"
            lowers = -50
            uppers = 50
        else:
            units = "NDVI"
            cmap = "RdYlGn"
            lowers = 0.2
            uppers = 0.8

        gdf = query_measurements(variable=variable, date=date)
        # lowers = gdf[variable].quantile(0.02)
        # uppers = gdf[variable].quantile(0.98)
        fig = px.choropleth_map(
            gdf,
            geojson=gdf.geometry,
            locations=gdf.index,
            color=variable,
            color_continuous_scale=cmap,
            range_color=(lowers, uppers),
            map_style="carto-positron",
            zoom=5.25,
            center={"lat": 40, "lon": -3},
            opacity=0.5,
            labels={variable: units},
        )
        return fig

    @app.callback(
        Output(component_id="date-filter", component_property="min_date_allowed"),
        Output(component_id="date-filter", component_property="max_date_allowed"),
        Output(component_id="date-filter", component_property="date"),
        Input(component_id="variable-filter", component_property="value"),
        Input(component_id="date-filter", component_property="date"),
    )
    def update_date_picker(variable, selected_date):
        ndvi_dates

        if variable == "ndvi":
            min_ndvi_date = ndvi_dates.min().strftime("%Y-%m-%d")
            max_ndvi_date = ndvi_dates.max().strftime("%Y-%m-%d")
            selected_date = pd.to_datetime(selected_date)

            if selected_date not in ndvi_dates:
                closest_date = ndvi_dates.iloc[
                    (ndvi_dates - selected_date).abs().argmin()
                ]
                selected_date = closest_date.strftime("%Y-%m-%d")

            return min_ndvi_date, max_ndvi_date, selected_date
        else:
            return date(1950, 1, 1), date(2024, 7, 15), selected_date
