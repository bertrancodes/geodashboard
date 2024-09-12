import dash

from app_callbacks import register_callbacks
from app_layout import layout
from definitions import ASSETS_PATH

# External stylesheets
external_stylesheets = [
    {
        "href": (
            "https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap"
        ),
        "rel": "stylesheet",
    },
]

# Initialize the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    assets_folder=ASSETS_PATH,  # Assuming ASSETS_PATH is defined in definitions.py
)

app.title = "Geodashboard"

# Set the layout
app.layout = layout

# Register the callbacks
register_callbacks(app)

# Run the server
if __name__ == "__main__":
    app.run_server(debug=True)
