# /sections/helpers/query_IDC.py

import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import plotly.express as px
import polars as pl
import pydeck as pdk
import requests
import streamlit as st
from pyproj import Transformer

from sections.helpers.save_excel_streamlit import display_dataframe_with_excel_download

logging.basicConfig(level=logging.DEBUG)

# Columns to keep from the API response, in display order
RESULT_COLUMNS = [
    "egid", "annee", "indice", "sre", "adresse", "npa", "commune",
    "destination",
    "agent_energetique_1", "quantite_agent_energetique_1", "unite_agent_energetique_1",
    "agent_energetique_2", "quantite_agent_energetique_2", "unite_agent_energetique_2",
    "agent_energetique_3", "quantite_agent_energetique_3", "unite_agent_energetique_3",
    "date_debut_periode", "date_fin_periode", "date_saisie",
    "indice_moy2", "annees_concernees_moy_2",
    "indice_moy3", "annees_concernees_moy_3",
    "id_concessionnaire", "nbre_preneur",
]


def make_request(
    offset: int,
    fields: str,
    url: str,
    chunk_size: int,
    table_name: str,
    geometry: bool,
    egid: Union[int, List[int]],
) -> Optional[List[Dict]]:
    """
    Query the SITG ArcGIS REST API for one or multiple EGIDs.

    Returns a list of dicts (attributes + geometry if requested), or None on error.
    Non-geometry path returns deduplicated records sorted by egid/annee.
    """
    where_clause = (
        f"egid IN ({','.join(map(str, egid))})" if isinstance(egid, list)
        else f"egid={egid}"
    )
    params = {
        "where": where_clause,
        "outFields": fields,
        "returnGeometry": str(geometry).lower(),
        "f": "json",
        "resultOffset": offset,
        "resultRecordCount": chunk_size,
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if "features" not in data:
            logging.warning(f"{table_name} → 'features' not found at offset {offset}")
            return None

        features = data["features"]

        if geometry:
            return [
                {"attributes": f["attributes"], "geometry": f["geometry"]}
                for f in features
            ]

        # --- Non-geometry path: parse and clean with Polars ---
        raw_records = [f["attributes"] for f in features]
        df = (
            pl.from_dicts(raw_records)
            .select(RESULT_COLUMNS)
            # Epoch ms → Datetime
            .with_columns([
                pl.col("date_debut_periode").cast(pl.Datetime("ms")),
                pl.col("date_fin_periode").cast(pl.Datetime("ms")),
                pl.col("date_saisie").cast(pl.Datetime("ms")),
                pl.col("npa").cast(pl.Int64),
                pl.col("quantite_agent_energetique_1").cast(pl.Float64),
                pl.col("quantite_agent_energetique_2").cast(pl.Float64),
                pl.col("quantite_agent_energetique_3").cast(pl.Float64),
            ])
            # Keep only the most recent saisie per (egid, annee)
            .sort(["egid", "annee", "date_saisie"], descending=[False, False, True])
            .unique(subset=["egid", "annee"], keep="first")
            .sort(["egid", "annee"])
        )

        return df.to_dicts()

    except requests.exceptions.RequestException as e:
        logging.error(f"{table_name} → Request error at offset {offset}: {e}")
    except json.JSONDecodeError:
        logging.error(f"{table_name} → JSON decode error at offset {offset}")

    return None


@st.cache_data
def convert_geometry_for_streamlit(data: List[Dict]) -> Tuple:
    """
    Convert polygon rings from LV95 (EPSG:2056) to WGS84 (EPSG:4326).
    Returns a GeoJSON FeatureCollection and the centroid [lon, lat].
    """
    transformer = Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)
    features = []
    all_points = []

    for item in data:
        if "geometry" not in item or "rings" not in item["geometry"]:
            continue

        new_rings = []
        for ring in item["geometry"]["rings"]:
            new_ring = []
            for x, y in ring:
                lon, lat = transformer.transform(x, y)
                new_ring.append([lon, lat])
                all_points.append([lon, lat])
            new_rings.append(new_ring)

        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": new_rings},
            "properties": item["attributes"],
        })

    geojson = {"type": "FeatureCollection", "features": features}
    centroid = np.mean(all_points, axis=0)
    return geojson, centroid


# NOTE: @st.cache_data removed — this function renders a Streamlit widget,
# caching it has no effect and may cause widget identity issues.
def show_map(data: List[Dict], centroid: Tuple[float, float]) -> None:
    """Render a PyDeck GeoJSON map centred on the selected buildings."""
    layer = pdk.Layer(
        "GeoJsonLayer",
        data,
        opacity=0.8,
        stroked=False,
        filled=True,
        extruded=False,
        get_fill_color=[255, 0, 0, 200],
        get_line_color=[0, 0, 0],
        pickable=True,
        auto_highlight=True,
    )
    view_state = pdk.ViewState(
        latitude=centroid[1],
        longitude=centroid[0],
        zoom=17,
        pitch=45,
    )
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/light-v9",
        tooltip={
            "html": "<b>EGID:</b> {egid}<br/><b>Adresse:</b> {adresse}<br/><b>SRE:</b> {sre} m²",
            "style": {"backgroundColor": "steelblue", "color": "white"},
        },
    )
    st.pydeck_chart(deck)


def show_dataframe(data: List[Dict]) -> None:
    """Display IDC data table with Excel download.

    Columns are already selected and sorted by make_request — no need to reprocess.
    """
    df = pl.from_dicts(data)
    # display_dataframe_with_excel_download expects a pandas DataFrame
    display_dataframe_with_excel_download(df.to_pandas())


@st.cache_data
def get_adresses_egid() -> pl.DataFrame:
    """Load all address/EGID pairs from the local SQLite database."""
    conn = sqlite3.connect("adresses_egid.db")
    try:
        return pl.read_database(
            "SELECT * FROM adresses_egid ORDER BY adresse", conn
        )
    finally:
        conn.close()


@st.cache_data
def create_barplot(data_df: List[Dict], nom_projet: str) -> None:
    """
    Render a grouped bar chart of IDC by year and address.

    Missing years are filled with 0 using a cross-join on the full year range,
    avoiding nested loops.
    """
    df = pl.from_dicts(data_df).select(["adresse", "egid", "annee", "indice"])

    current_year = datetime.now().year
    years_df = pl.DataFrame({"annee": list(range(2011, current_year + 1))})

    # Cross-join all address/egid pairs with all years, then fill gaps
    df_full = (
        df.select(["adresse", "egid"]).unique()
        .join(years_df, how="cross")
        .join(df, on=["adresse", "egid", "annee"], how="left")
        .with_columns(pl.col("indice").fill_null(0))
        .sort(["annee", "adresse", "egid"])
        .with_columns([
            (pl.col("adresse") + " - " + pl.col("egid").cast(pl.Utf8)).alias("adresse_egid"),
            pl.when(pl.col("indice") > 0)
              .then(pl.col("indice").cast(pl.Utf8))
              .otherwise(pl.lit(""))
              .alias("text"),
        ])
    )

    # Compute right margin based on longest legend label
    longest_label = df_full["adresse_egid"].str.len_chars().max()
    right_margin = longest_label * 8 + 25

    # Plotly Express works directly with Polars DataFrames (v0.8+)
    fig = px.bar(
        df_full,
        x="annee",
        y="indice",
        color="adresse_egid",
        barmode="group",
        labels={"annee": "Année", "indice": "Indice [MJ/m²]"},
        title=f"Indice par Année et Adresse pour {nom_projet}",
        text="text",
        height=400,
    )

    fig.update_traces(textposition="outside", texttemplate="%{text}", cliponaxis=False)
    fig.update_layout(
        xaxis_title="Année",
        yaxis_title="Indice [MJ/m²]",
        legend_title="Adresse - EGID",
        xaxis={
            "type": "category",
            "tickangle": 0,
            "gridcolor": "rgba(211, 211, 211, 0.2)",
            "gridwidth": 0.1,
            "tickfont": {"size": 12},
        },
        yaxis={
            "range": [0, df_full["indice"].max() * 1.15],
            "gridcolor": "rgba(211, 211, 211, 0.2)",
            "gridwidth": 0.1,
            "tickfont": {"size": 12},
        },
        margin=dict(t=50, r=right_margin, b=50, l=50),
        legend=dict(
            yanchor="top", y=1, xanchor="left", x=1,
            bgcolor="rgba(255, 255, 255, 0.8)",
            borderwidth=0,
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        autosize=False,
        font=dict(size=12, family="Arial", color="black"),
        title={"y": 0.95, "x": 0.5, "xanchor": "center", "yanchor": "top"},
    )

    st.plotly_chart(
        fig,
        use_container_width=False,
        config={
            "toImageButtonOptions": {
                "format": "png",
                "filename": "indice_par_annee",
                "height": 500,
                "width": 1400,
                "scale": 2,
            },
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": [
                "zoom2d", "pan2d", "select2d", "lasso2d",
                "zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d",
            ],
        },
    )