"""FastAPI backend for the Next.js frontend (the spec's "profi út").

Read-only: serves the same SQLite database etl/run.py populates. The
frontend never touches the DB directly.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "holaviz.sqlite3"

app = FastAPI(title="Hol a víz? API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def query(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    if not DB_PATH.exists():
        raise HTTPException(status_code=503, detail="No data yet - run etl/run.py first.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


class Station(BaseModel):
    voa: str
    river: str
    name: str
    display_name: str | None
    category: str
    lat: float | None
    lon: float | None
    lkv_cm: float | None
    lnv_cm: float | None
    kf1_cm: float | None
    latest_measured_at: str | None
    water_level_cm: float | None
    discharge_m3s: float | None
    water_temp_c: float | None
    previous_water_level_cm: float | None


class Measurement(BaseModel):
    measured_at: str
    water_level_cm: float | None
    discharge_m3s: float | None
    water_temp_c: float | None


class SoilPoint(BaseModel):
    location: str
    lat: float
    lon: float
    measured_at: str
    shallow_vwc: float | None
    deep_vwc: float | None


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "db_exists": DB_PATH.exists()}


@app.get("/api/stations", response_model=list[Station])
def list_stations():
    rows = query(
        """
        SELECT s.voa, s.river, s.name, s.display_name, s.category,
               s.lat, s.lon, s.lkv_cm, s.lnv_cm, s.kf1_cm,
               latest.measured_at AS latest_measured_at,
               latest.water_level_cm, latest.discharge_m3s, latest.water_temp_c,
               prev.water_level_cm AS previous_water_level_cm
        FROM stations s
        LEFT JOIN measurements latest
            ON latest.id = (
                SELECT id FROM measurements WHERE station_voa = s.voa ORDER BY measured_at DESC LIMIT 1
            )
        LEFT JOIN measurements prev
            ON prev.id = (
                SELECT id FROM measurements
                WHERE station_voa = s.voa AND measured_at < latest.measured_at
                ORDER BY measured_at DESC LIMIT 1
            )
        ORDER BY s.category, s.river, s.name
        """
    )
    return [dict(r) for r in rows]


@app.get("/api/stations/{voa}/history", response_model=list[Measurement])
def station_history(voa: str, days: int = 7):
    # Relative to this station's own latest reading (not wall-clock "now")
    # to match how the Streamlit dashboard windows history, and to sidestep
    # any UTC-vs-source-local skew in the stored measured_at strings.
    rows = query(
        """
        SELECT measured_at, water_level_cm, discharge_m3s, water_temp_c
        FROM measurements
        WHERE station_voa = ?
          AND measured_at >= (
              SELECT datetime(MAX(measured_at), ?) FROM measurements WHERE station_voa = ?
          )
        ORDER BY measured_at
        """,
        (voa, f"-{days} days", voa),
    )
    return [dict(r) for r in rows]


@app.get("/api/soil-moisture", response_model=list[SoilPoint])
def soil_moisture():
    rows = query(
        """
        SELECT location, lat, lon, measured_at, shallow_vwc, deep_vwc
        FROM soil_moisture
        WHERE measured_at = (SELECT MAX(measured_at) FROM soil_moisture)
        ORDER BY shallow_vwc
        """
    )
    return [dict(r) for r in rows]
