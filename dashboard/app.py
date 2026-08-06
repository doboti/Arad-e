"""Streamlit MVP dashboard (Milestone 3).

Reads the SQLite database etl/run.py populates and renders hero numbers
plus a 7-day history chart per station, with the historical LKV/LNV
(min/max) drawn in for context as the spec asks for.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "holaviz.sqlite3"

# Display order matching the spec's hero-number section (Balaton, Duna, Tisza).
RIVER_ORDER = {"Balaton": 0, "Duna": 1, "Tisza": 2}

st.set_page_config(page_title="Hol a víz?", page_icon="💧", layout="wide")


def ordered_station_ids(df: pd.DataFrame) -> list[str]:
    latest_per_station = df.sort_values("measured_at").groupby("voa").last().reset_index()
    latest_per_station["order"] = latest_per_station["river"].map(RIVER_ORDER).fillna(99)
    return latest_per_station.sort_values(["order", "name"])["voa"].tolist()


@st.cache_data(ttl=300)
def load_measurements() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(
            """
            SELECT s.voa, s.river, s.name, s.lkv_cm, s.lnv_cm,
                   m.measured_at, m.water_level_cm, m.discharge_m3s, m.water_temp_c
            FROM measurements m
            JOIN stations s ON s.voa = m.station_voa
            ORDER BY m.measured_at
            """,
            conn,
            parse_dates=["measured_at"],
        )
    finally:
        conn.close()


def render_hero_numbers(df: pd.DataFrame) -> None:
    stations = ordered_station_ids(df)
    cols = st.columns(len(stations))
    for col, voa in zip(cols, stations):
        station_df = df[df["voa"] == voa].sort_values("measured_at")
        latest = station_df.iloc[-1]
        previous = station_df.iloc[-2]["water_level_cm"] if len(station_df) > 1 else None
        delta = None if previous is None else latest["water_level_cm"] - previous
        with col:
            st.metric(
                label=f"{latest['river']} – {latest['name']}",
                value=f"{latest['water_level_cm']:.0f} cm",
                delta=None if delta is None else f"{delta:+.0f} cm",
            )
            st.caption(f"Mérve: {latest['measured_at']:%Y-%m-%d %H:%M}")


def render_history_charts(df: pd.DataFrame) -> None:
    cutoff = df["measured_at"].max() - pd.Timedelta(days=7)
    recent = df[df["measured_at"] >= cutoff]

    for voa in ordered_station_ids(recent):
        station_df = recent[recent["voa"] == voa].sort_values("measured_at")
        first = station_df.iloc[0]
        st.markdown(f"**{first['river']} – {first['name']}**")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=station_df["measured_at"],
                y=station_df["water_level_cm"],
                mode="lines+markers",
                name="Vízállás (cm)",
                line=dict(color="#1f77b4"),
            )
        )
        if pd.notna(first["lnv_cm"]):
            fig.add_hline(
                y=first["lnv_cm"], line_dash="dot", line_color="crimson",
                annotation_text="LNV (történelmi max.)", annotation_position="top left",
            )
        if pd.notna(first["lkv_cm"]):
            fig.add_hline(
                y=first["lkv_cm"], line_dash="dot", line_color="orange",
                annotation_text="LKV (történelmi min.)", annotation_position="bottom left",
            )

        fig.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_title=None,
            yaxis_title="cm",
            showlegend=False,
        )
        if len(station_df) == 1:
            # A single point gives plotly nothing to size the time axis by,
            # so it falls back to a microsecond-wide range. Pad it manually.
            center = station_df["measured_at"].iloc[0]
            fig.update_xaxes(range=[center - pd.Timedelta(hours=12), center + pd.Timedelta(hours=12)])

        st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    st.title("💧 Hol a víz?")
    st.caption("Valós idejű hazai víz- és aszályfigyelő - MVP")

    df = load_measurements()
    if df.empty:
        st.warning("Nincs még adat. Futtasd az `etl/run.py` szkriptet, hogy legyen mit megjeleníteni.")
        return

    render_hero_numbers(df)
    st.divider()
    st.subheader("Elmúlt 7 nap")
    render_history_charts(df)


if __name__ == "__main__":
    main()
