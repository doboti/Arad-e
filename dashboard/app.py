"""Streamlit MVP dashboard.

Reads the SQLite database etl/run.py populates and renders:
  - hero numbers for the spec's headline stations, plus a national soil
    moisture average standing in for the spec's "aszályindex"
  - a "Nagy tavaink" section (Balaton, Velencei-tó, Tisza-tó)
  - a "Folyók és vízgyűjtők" section (Duna, Tisza)
  - an "Aszály és talajnedvesség" section comparing shallow/deep soil
    moisture across sample locations, driest first
each history chart includes the historical LKV/LNV (min/max) as reference
lines for context, as the spec asks for.
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

# The four headline readings from the spec's "Kritikus mutatók" list.
HERO_STATIONS = [("Balaton", "Siófok"), ("Duna", "Budapest"), ("Duna", "Paks"), ("Tisza", "Szolnok")]

SECTION_TITLES = {"lakes": "Nagy tavaink", "rivers": "Folyók és vízgyűjtők"}

# Status colors/labels for the overview map, matching the spec's
# kék/zöld/sárga/piros (blue/green/yellow/red) scheme.
STATUS_STYLE = {
    "flood": ("#1f77b4", "Áradás"),
    "normal": ("#2ca02c", "Normál"),
    "low": ("#f1c40f", "Alacsony"),
    "critical": ("#e74c3c", "Kritikus aszály / kiszáradás"),
}

st.set_page_config(page_title="Hol a víz?", page_icon="💧", layout="wide")


def classify_status(level: float | None, lkv: float | None, lnv: float | None, kf1: float | None) -> str:
    """Heuristic status for the overview map.

    Uses the official I. fokozatú flood-alert level (kf1) when vizugy.hu
    publishes one for that station; otherwise falls back to the station's
    position between its historical min (LKV) and max (LNV). The specific
    cutoffs (35% / 12%) aren't an official standard - just a reasonable
    default absent real defense-stage data for every station.
    """
    if level is None:
        return "normal"
    if kf1 is not None and level >= kf1:
        return "flood"
    if lkv is None or lnv is None or lnv <= lkv:
        return "normal"
    position = (level - lkv) / (lnv - lkv)
    if position >= 0.35:
        return "normal"
    if position >= 0.12:
        return "low"
    return "critical"


def label_for(row: pd.Series) -> str:
    return row["display_name"] or f"{row['river']} – {row['name']}"


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
            SELECT s.voa, s.river, s.name, s.category, s.display_name,
                   s.lkv_cm, s.lnv_cm, s.kf1_cm, s.lat, s.lon,
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


@st.cache_data(ttl=300)
def load_soil_moisture() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(
            "SELECT location, lat, lon, measured_at, shallow_vwc, deep_vwc FROM soil_moisture ORDER BY measured_at",
            conn,
            parse_dates=["measured_at"],
        )
    finally:
        conn.close()


def render_hero_numbers(df: pd.DataFrame, soil_df: pd.DataFrame) -> None:
    latest_per_station = df.sort_values("measured_at").groupby("voa").last().reset_index()
    hero_rows = []
    for river, name in HERO_STATIONS:
        match = latest_per_station[(latest_per_station["river"] == river) & (latest_per_station["name"] == name)]
        if not match.empty:
            hero_rows.append(match.iloc[0])

    n_cols = len(hero_rows) + (1 if not soil_df.empty else 0)
    if n_cols == 0:
        return
    cols = st.columns(n_cols)

    for col, latest in zip(cols, hero_rows):
        station_df = df[df["voa"] == latest["voa"]].sort_values("measured_at")
        previous = station_df.iloc[-2]["water_level_cm"] if len(station_df) > 1 else None
        delta = None if previous is None else latest["water_level_cm"] - previous
        with col:
            st.metric(
                label=label_for(latest),
                value=f"{latest['water_level_cm']:.0f} cm",
                delta=None if delta is None else f"{delta:+.0f} cm",
            )
            st.caption(f"Mérve: {latest['measured_at']:%Y-%m-%d %H:%M}")

    if not soil_df.empty:
        latest_soil = soil_df.sort_values("measured_at").groupby("location").last().reset_index()
        avg_shallow = latest_soil["shallow_vwc"].mean()
        with cols[-1]:
            st.metric(label="Talajnedvesség (országos átlag)", value=f"{avg_shallow * 100:.0f}%")
            st.caption(f"{len(latest_soil)} mintaponton, felső ~9 cm")


def render_map(df: pd.DataFrame) -> None:
    latest = df.sort_values("measured_at").groupby("voa").last().reset_index()
    latest = latest.dropna(subset=["lat", "lon"])
    if latest.empty:
        return

    latest["status"] = latest.apply(
        lambda r: classify_status(r["water_level_cm"], r["lkv_cm"], r["lnv_cm"], r["kf1_cm"]), axis=1
    )
    latest["color"] = latest["status"].map(lambda s: STATUS_STYLE[s][0])
    latest["label"] = latest.apply(label_for, axis=1)
    latest["hover"] = latest.apply(
        lambda r: f"{r['label']}<br>{r['water_level_cm']:.0f} cm<br>{STATUS_STYLE[r['status']][1]}", axis=1
    )

    fig = go.Figure(
        go.Scattermapbox(
            lat=latest["lat"],
            lon=latest["lon"],
            mode="markers+text",
            marker=dict(size=16, color=latest["color"]),
            text=latest["label"],
            textposition="top center",
            hovertext=latest["hover"],
            hoverinfo="text",
        )
    )
    fig.update_layout(
        mapbox=dict(style="open-street-map", center=dict(lat=47.16, lon=19.5), zoom=6.1),
        margin=dict(l=0, r=0, t=0, b=0),
        height=480,
    )
    st.plotly_chart(fig, use_container_width=True)

    legend = "&nbsp;&nbsp;&nbsp;".join(
        f'<span style="color:{color}">●</span> {label}' for color, label in STATUS_STYLE.values()
    )
    st.markdown(legend, unsafe_allow_html=True)


def render_history_charts(df: pd.DataFrame, category: str) -> None:
    cutoff = df["measured_at"].max() - pd.Timedelta(days=7)
    recent = df[(df["measured_at"] >= cutoff) & (df["category"] == category)]
    if recent.empty:
        st.caption("Nincs adat ehhez a szakaszhoz.")
        return

    for voa in ordered_station_ids(recent):
        station_df = recent[recent["voa"] == voa].sort_values("measured_at")
        first = station_df.iloc[0]
        latest = station_df.iloc[-1]

        header = f"**{label_for(first)}**"
        if category == "rivers" and pd.notna(latest["discharge_m3s"]):
            header += f" &nbsp;·&nbsp; vízhozam: {latest['discharge_m3s']:.0f} m³/s"
        st.markdown(header)

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
            height=300,
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


def render_drought_section(soil_df: pd.DataFrame) -> None:
    if soil_df.empty:
        st.caption("Nincs talajnedvesség-adat.")
        return

    latest = soil_df.sort_values("measured_at").groupby("location").last().reset_index()
    latest = latest.sort_values("shallow_vwc")  # driest first - where drought risk is highest

    fig = go.Figure()
    fig.add_trace(go.Bar(x=latest["location"], y=latest["shallow_vwc"] * 100, name="Felső réteg (~0–9 cm)", marker_color="#c47f17"))
    fig.add_trace(go.Bar(x=latest["location"], y=latest["deep_vwc"] * 100, name="Mélyebb réteg (~9–81 cm)", marker_color="#1f77b4"))
    fig.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis_title="Talajnedvesség (%)",
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Open-Meteo modellezett talajnedvesség-adatai néhány mintaponton - tájékoztató jellegű, "
        "nem hivatalos aszálytérkép. Mérve: " + f"{latest['measured_at'].max():%Y-%m-%d %H:%M}"
    )


def main() -> None:
    st.title("💧 Hol a víz?")
    st.caption("Valós idejű hazai víz- és aszályfigyelő - MVP")

    df = load_measurements()
    soil_df = load_soil_moisture()
    if df.empty:
        st.warning("Nincs még adat. Futtasd az `etl/run.py` szkriptet, hogy legyen mit megjeleníteni.")
        return

    render_hero_numbers(df, soil_df)

    st.divider()
    st.subheader("Országos helyzetkép")
    render_map(df)

    for category, title in SECTION_TITLES.items():
        st.divider()
        st.subheader(title)
        render_history_charts(df, category)

    st.divider()
    st.subheader("Aszály és talajnedvesség")
    render_drought_section(soil_df)


if __name__ == "__main__":
    main()
