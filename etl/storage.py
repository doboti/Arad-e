"""SQLite storage for water-level measurements.

Milestone 2 of the roadmap: persist each scrape so the dashboard can later
plot history instead of just the latest reading. SQLite is the MVP choice
from the spec - a single file, no server, good enough for hourly writes.
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from scraper import StationReading

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "holaviz.sqlite3"

SCHEMA = """
CREATE TABLE IF NOT EXISTS stations (
    voa           TEXT PRIMARY KEY,
    river         TEXT NOT NULL,
    name          TEXT NOT NULL,
    cross_section TEXT,
    lkv_cm        REAL,
    lnv_cm        REAL
);

CREATE TABLE IF NOT EXISTS measurements (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    station_voa    TEXT NOT NULL REFERENCES stations(voa),
    measured_at    TEXT NOT NULL,
    water_level_cm REAL,
    discharge_m3s  REAL,
    water_temp_c   REAL,
    fetched_at     TEXT NOT NULL,
    UNIQUE(station_voa, measured_at)
);
"""


_LEADING_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def parse_number(raw: str) -> float | None:
    """"697 cm" -> 697.0, "60.76 m^3/s" -> 60.76, "-" -> None.

    Matches only the leading numeric token so unit suffixes containing
    digits (e.g. the "3" in "m^3/s") are never absorbed into the value.
    """
    raw = raw.strip()
    if raw in ("", "-"):
        return None
    match = _LEADING_NUMBER.match(raw)
    return float(match.group()) if match else None


def parse_measured_at(raw: str) -> str | None:
    """"2026.08.06. 11:00" -> "2026-08-06T11:00:00"."""
    raw = raw.strip()
    try:
        return datetime.strptime(raw, "%Y.%m.%d. %H:%M").isoformat()
    except ValueError:
        return None


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn


def save_readings(conn: sqlite3.Connection, readings: list[StationReading]) -> int:
    """Upsert station metadata and insert new measurement rows.

    Returns the number of new measurement rows actually inserted; readings
    whose measured_at timestamp is already stored for that station are
    silently skipped (safe to re-run the scraper as often as we like).
    """
    fetched_at = datetime.now(timezone.utc).isoformat()
    inserted = 0
    for r in readings:
        conn.execute(
            """
            INSERT INTO stations (voa, river, name, cross_section, lkv_cm, lnv_cm)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(voa) DO UPDATE SET
                river=excluded.river, name=excluded.name,
                cross_section=excluded.cross_section,
                lkv_cm=excluded.lkv_cm, lnv_cm=excluded.lnv_cm
            """,
            (r.voa, r.river, r.station, r.cross_section, parse_number(r.lkv_cm), parse_number(r.lnv_cm)),
        )

        measured_at = parse_measured_at(r.measured_at) or fetched_at
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO measurements
                (station_voa, measured_at, water_level_cm, discharge_m3s, water_temp_c, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                r.voa,
                measured_at,
                parse_number(r.water_level_cm),
                parse_number(r.discharge_m3s),
                parse_number(r.water_temp_c),
                fetched_at,
            ),
        )
        inserted += cur.rowcount

    conn.commit()
    return inserted
