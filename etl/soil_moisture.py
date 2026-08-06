"""Soil moisture collection (Module D: aszály / talajnedvesség).

The spec's own data-source table already recommends Open-Meteo for
weather; its free forecast API also exposes modelled soil moisture by
depth band, with no key and no scraping - a much lighter path than
scraping met.hu or processing Copernicus satellite imagery. We sample a
handful of points spread across Hungary's main agricultural regions and
blend Open-Meteo's five depth bands into two the dashboard can show
(shallow / deeper), rather than claiming an exact match to the spec's
0-20cm / 20-50cm framing that this data source doesn't cleanly offer.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests

API_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = 15

# Representative points spread across Hungary's main agricultural regions.
LOCATIONS = [
    ("Győr", 47.68, 17.63),
    ("Székesfehérvár", 47.19, 18.41),
    ("Kecskemét", 46.90, 19.69),
    ("Szeged", 46.25, 20.15),
    ("Debrecen", 47.53, 21.62),
    ("Nyíregyháza", 47.95, 21.72),
    ("Miskolc", 48.10, 20.78),
    ("Pécs", 46.07, 18.23),
]

SHALLOW_FIELDS = ["soil_moisture_0_to_1cm", "soil_moisture_1_to_3cm", "soil_moisture_3_to_9cm"]
DEEP_FIELDS = ["soil_moisture_9_to_27cm", "soil_moisture_27_to_81cm"]


@dataclass
class SoilReading:
    location: str
    lat: float
    lon: float
    measured_at: str
    shallow_vwc: float | None  # volumetric water content (0-1), blend of 0-9cm bands
    deep_vwc: float | None  # blend of 9-81cm bands


def _avg(*values: float | None) -> float | None:
    present = [v for v in values if v is not None]
    return sum(present) / len(present) if present else None


def fetch_readings() -> list[SoilReading]:
    resp = requests.get(
        API_URL,
        params={
            "latitude": ",".join(str(lat) for _, lat, _ in LOCATIONS),
            "longitude": ",".join(str(lon) for _, _, lon in LOCATIONS),
            "current": ",".join(SHALLOW_FIELDS + DEEP_FIELDS),
            "timezone": "Europe/Budapest",
        },
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    payload = resp.json()

    readings = []
    for (name, lat, lon), entry in zip(LOCATIONS, payload):
        current = entry.get("current", {})
        readings.append(
            SoilReading(
                location=name,
                lat=lat,
                lon=lon,
                measured_at=current.get("time", ""),
                shallow_vwc=_avg(*(current.get(f) for f in SHALLOW_FIELDS)),
                deep_vwc=_avg(*(current.get(f) for f in DEEP_FIELDS)),
            )
        )
    return readings
