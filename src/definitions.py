import os
from pathlib import Path

# PATHS
ROOT_DIR = Path(__file__).parent.parent
CONFIG_PATH = ROOT_DIR / "conf" / "configuration.conf"
DATA_PATH = ROOT_DIR / "data"
LOG_PATH = ROOT_DIR / "log"
IMG_PATH = ROOT_DIR / "images"
SQL_PATH = ROOT_DIR / "sql"
ASSETS_PATH = ROOT_DIR / "assets"

# DATABASE PARAMS
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")
