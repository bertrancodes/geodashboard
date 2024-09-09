from datetime import date

import matplotlib.pyplot as plt
import numpy as np
from astral import LocationInfo
from astral.sun import sun

from definitions import IMG_PATH


def time_to_seconds(time: date) -> float:
    """Cast a date to seconds since midnight"""
    total_seconds = (
        (time.hour * 60 + time.minute) * 60 + time.second + time.microsecond / 10e6
    )
    return total_seconds


def calculate_sun_times(
    city_name: str,
    country: str,
    timezone: str,
    latitude: float,
    longitude: float,
    start_year: int,
    end_year: int,
) -> tuple[float, float]:
    """
    Compute sunrise and sunset in seconds since midnight for January 1st for a
    range of years
    """
    city = LocationInfo(city_name, country, timezone, latitude, longitude)
    years = range(start_year, end_year + 1)

    sunrise_seconds = np.zeros(len(years))
    sunset_seconds = np.zeros(len(years))

    for n, year in enumerate(years):
        s = sun(city.observer, date=date(year, 1, 1))
        sunrise_seconds[n] = time_to_seconds(s["sunrise"])
        sunset_seconds[n] = time_to_seconds(s["sunset"])

    return sunrise_seconds, sunset_seconds


def plot_sun_times(
    cities: list, start_year: int = 1950, end_year: int = 2025
) -> tuple[plt.Figure, plt.Axes]:
    """
    Plot sunrise and sunset anomalies for a set of cities between a range of
    years
    """
    sunrises = []
    sunsets = []
    labels = []

    for city in cities:
        city_name, country, timezone, latitude, longitude = city
        sunrise_seconds, sunset_seconds = calculate_sun_times(
            city_name, country, timezone, latitude, longitude, start_year, end_year
        )

        sunrises.append(sunrise_seconds - np.mean(sunrise_seconds))
        sunsets.append(sunset_seconds - np.mean(sunset_seconds))
        labels.append(f"{city_name}")

    fig, axs = plt.subplots(nrows=2, ncols=1, figsize=(14, 8))
    axs[0].boxplot(sunrises, labels=labels, vert=False)
    axs[1].boxplot(sunsets, labels=labels, vert=False)
    axs[0].set_xlabel("Tiempo (s)")
    axs[1].set_xlabel("Tiempo (s)")
    axs[0].set_ylabel("Ciudad")
    axs[1].set_ylabel("Ciudad")
    axs[0].set_title(f"Alba para el 1 de enero ({start_year}-{end_year})")
    axs[1].set_title(f"Puesta del Sol para el 1 de enero ({start_year}-{end_year})")
    fig.suptitle(
        "Anomalía para el alba y la puesta del Sol",
        fontsize=18,
        fontname="DejaVu Serif",
        fontweight="bold",
    )
    fig.tight_layout(pad=2.5)

    return fig, axs


if __name__ == "__main__":
    # Use cities from all the country to have a good geospatial range
    cities = [
        ("València", "España", "Europa/Berlín", 39.47391, -0.37966),
        ("Barcelona", "España", "Europe/Berlín", 41.38879, 2.15899),
        ("Madrid", "España", "Europa/Berlín", 40.4165, -3.70256),
        ("Bilbao", "España", "Europa/Berlín", 43.262985, -2.935013),
        ("Sevilla", "España", "Europa/Berlín", 37.3833, -5.9833),
        ("Cáceres", "España", "Europa/Berlín", 39.4731, -6.3711),
        ("Santiago de Compostela", "España", "Europa/Berlín", 42.88, -8.53),
    ]

    fig, _ = plot_sun_times(cities, start_year=1950, end_year=2025)
    fig.savefig(IMG_PATH / "sunrise_sunset_anomaly.png", dpi=300)
