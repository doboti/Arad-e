"""Scraper for the "Hol a víz?" tracked stations.

vizugy.hu has no public JSON API. Its homepage instead renders the entire
national station list server-side into parallel JavaScript arrays (one
array per field, all indexed the same way) that a client-side map widget
reads on hover. We fetch that homepage HTML and parse those arrays
directly, which is far more stable than scraping a rendered table.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, replace

import requests

SOURCE_URL = "https://www.vizugy.hu/"
USER_AGENT = "Mozilla/5.0 (compatible; HolAVizBot/0.1; +https://github.com/)"
REQUEST_TIMEOUT = 15

# Field name -> JS array variable name on the vizugy.hu homepage.
ARRAY_FIELDS = {
    "voa": "AllomasVOA",  # stable station GUID, used as the external ID
    "river": "VizfolyasNev",
    "station": "VizmerceNev",
    "cross_section": "Szelveny",
    "water_level_cm": "Vizallas",
    "discharge_m3s": "Vizhozam",
    "water_temp_c": "Vizho",
    "measured_at": "UtolsoMeresIdopontja",
    "lkv_cm": "LKV",  # Legkisebb Vízállás - historical minimum
    "lnv_cm": "LNV",  # Legnagyobb Vízállás - historical maximum
    "kf1_cm": "IKeszultsegiSzint",  # I. fokozatú (official) flood-alert level, where defined
}

# Tracked stations: (river, station-name substring as it appears on
# vizugy.hu, dashboard section, display-name override, lat, lon).
#
# "lakes" mirrors the spec's "Nagy Tavaink" module, "rivers" mirrors
# "Folyók és Vízgyűjtők". Balaton/Duna(Bp)/Tisza(Szolnok) also double as
# the dashboard's hero numbers. Coordinates are the settlement's, not the
# exact gauge - close enough for a national overview map.
TARGET_STATIONS = [
    ("Balaton", "Siófok", "lakes", None, 46.9057, 18.0525),
    ("Velencei-tó", "Agárd", "lakes", None, 47.1898, 18.6142),
    ("Tisza", "Kisköre felső", "lakes", "Tisza-tó (Kisköre)", 47.4939, 20.0994),
    ("Duna", "Budapest", "rivers", None, 47.4979, 19.0402),
    ("Duna", "Paks", "rivers", None, 46.6229, 18.8529),
    ("Tisza", "Szolnok", "rivers", None, 47.1621, 20.1826),
]


@dataclass
class StationReading:
    voa: str
    river: str
    station: str
    cross_section: str
    water_level_cm: str
    discharge_m3s: str
    water_temp_c: str
    measured_at: str
    lkv_cm: str
    lnv_cm: str
    kf1_cm: str
    category: str = ""
    display_name: str | None = None
    lat: float | None = None
    lon: float | None = None


def fetch_html() -> str:
    resp = requests.get(SOURCE_URL, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return resp.text


def _extract_js_array(html: str, var_name: str) -> list[str]:
    match = re.search(rf"{re.escape(var_name)}\s*=\s*new Array\((.*?)\);", html, re.S)
    if not match:
        raise ValueError(f"Could not find JS array '{var_name}' on the page - vizugy.hu markup may have changed.")
    values = re.findall(r"'((?:[^'\\]|\\.)*)'", match.group(1))
    # A few fields (e.g. discharge) embed "m<sup>3</sup>/s" - collapse to plain text.
    return [re.sub(r"<sup>(.*?)</sup>", r"^\1", v) for v in values]


def parse_stations(html: str) -> list[StationReading]:
    columns = {field: _extract_js_array(html, var) for field, var in ARRAY_FIELDS.items()}

    lengths = {field: len(values) for field, values in columns.items()}
    if len(set(lengths.values())) != 1:
        raise ValueError(f"vizugy.hu station arrays have mismatched lengths: {lengths}")

    count = next(iter(lengths.values()))
    return [StationReading(**{field: columns[field][i] for field in ARRAY_FIELDS}) for i in range(count)]


def filter_targets(stations: list[StationReading]) -> list[StationReading]:
    result = []
    for river, station_hint, category, display_name, lat, lon in TARGET_STATIONS:
        match = next((s for s in stations if s.river == river and station_hint in s.station), None)
        if match is None:
            print(f"WARNING: no match found for {river} / {station_hint}", file=sys.stderr)
            continue
        result.append(replace(match, category=category, display_name=display_name, lat=lat, lon=lon))
    return result


def main() -> None:
    html = fetch_html()
    stations = parse_stations(html)
    targets = filter_targets(stations)

    if not targets:
        print("No target stations found - source page structure likely changed.", file=sys.stderr)
        sys.exit(1)

    print(f"Hol a víz? - aktuális vízállások ({SOURCE_URL})\n")
    for s in targets:
        label = s.display_name or f"{s.river} ({s.station})"
        print(f"[{s.category}] {label} - {s.cross_section}")
        print(f"  Vízállás: {s.water_level_cm}   Mérve: {s.measured_at}")
        print(f"  Vízhozam: {s.discharge_m3s}   Vízhőfok: {s.water_temp_c}")
        print(f"  LKV: {s.lkv_cm}   LNV: {s.lnv_cm}")
        print()


if __name__ == "__main__":
    main()
