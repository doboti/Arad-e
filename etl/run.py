"""Scheduled collection entry point (Milestone 2).

Fetches current water levels and persists them to SQLite. Meant to be
invoked hourly (e.g. by GitHub Actions) rather than run interactively -
use scraper.py directly for a quick console check.
"""

from __future__ import annotations

import sys

import storage
from scraper import fetch_html, filter_targets, parse_stations


def main() -> None:
    html = fetch_html()
    stations = parse_stations(html)
    targets = filter_targets(stations)

    if not targets:
        print("No target stations found - source page structure likely changed.", file=sys.stderr)
        sys.exit(1)

    conn = storage.connect()
    try:
        inserted = storage.save_readings(conn, targets)
    finally:
        conn.close()

    print(f"Saved {len(targets)} station reading(s), {inserted} new measurement row(s) -> {storage.DB_PATH}")


if __name__ == "__main__":
    main()
