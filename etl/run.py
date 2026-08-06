"""Scheduled collection entry point (Milestone 2).

Fetches current water levels and persists them to SQLite. Meant to be
invoked hourly (e.g. by GitHub Actions) rather than run interactively -
use scraper.py directly for a quick console check.
"""

from __future__ import annotations

import sys

import storage
from scraper import fetch_html, filter_targets, parse_stations
from soil_moisture import fetch_readings as fetch_soil_readings


def main() -> None:
    html = fetch_html()
    stations = parse_stations(html)
    targets = filter_targets(stations)

    if not targets:
        print("No target stations found - source page structure likely changed.", file=sys.stderr)
        sys.exit(1)

    soil_readings = fetch_soil_readings()

    conn = storage.connect()
    try:
        inserted = storage.save_readings(conn, targets)
        soil_inserted = storage.save_soil_readings(conn, soil_readings)
    finally:
        conn.close()

    print(f"Saved {len(targets)} station reading(s), {inserted} new measurement row(s) -> {storage.DB_PATH}")
    print(f"Saved {len(soil_readings)} soil moisture reading(s), {soil_inserted} new row(s)")


if __name__ == "__main__":
    main()
