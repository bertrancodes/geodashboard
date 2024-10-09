from datetime import date

from dash import dcc, html

from app_data_fetcher import blank_figure, variables

layout = html.Div(
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
                        html.Div(children="Date (DD-MM-YYYY)", className="menu-title"),
                        dcc.DatePickerSingle(
                            id="date-filter",
                            min_date_allowed=date(1950, 1, 1),
                            max_date_allowed=date(2024, 7, 15),
                            initial_visible_month=date(2020, 1, 1),
                            date=date(2020, 1, 1),
                            display_format="DD-MM-YYYY",
                        ),
                    ]
                ),
            ],
            className="menu",
        ),
        dcc.Loading(
            id="loading-spinner",
            type="circle",
            overlay_style={"visibility": "visible", "filter": "blur(2px)"},
            children=[
                dcc.Graph(
                    id="graph",
                    figure=blank_figure(),
                    style={
                        "width": "125vh",
                        "height": "85vh",
                        "marginLeft": "auto",
                        "marginRight": "auto",
                    },
                )
            ],
            fullscreen=False,
        ),
        # Data sources
        html.Div(
            children=[
                html.P(
                    children=[
                        "Data sources: ",
                        html.A(
                            "Instituto Geográfico Nacional",
                            href="https://www.ign.es/web/ign/portal",
                            target="_blank",
                            style={"color": "#1e90ff", "text-decoration": "none"},
                        ),
                        ", ",
                        html.A(
                            "ERA5-Land",
                            href="https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview",
                            target="_blank",
                            style={"color": "#1e90ff", "text-decoration": "none"},
                        ),
                        ", ",
                        html.A(
                            "MODIS-Terra",
                            href="https://lpdaac.usgs.gov/products/mod13q1v006/",
                            target="_blank",
                            style={"color": "#1e90ff", "text-decoration": "none"},
                        ),
                    ],
                    style={
                        "textAlign": "center",
                        "paddingTop": "20px",
                        "fontSize": "16px",
                    },
                ),
            ],
            className="data-sources",
        ),
    ]
)
