# /sections/helpers/query_IDC.py

import json
import logging
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import polars as pl
import pydeck as pdk
import requests
import streamlit as st
from pyproj import Transformer

from sections.helpers.save_excel_streamlit import display_dataframe_with_excel_download

logging.basicConfig(level=logging.DEBUG)

# Columns to keep from the API response, in display order
RESULT_COLUMNS = [
    "egid",
    "annee",
    "indice",
    "sre",
    "adresse",
    "npa",
    "commune",
    "destination",
    "agent_energetique_1",
    "quantite_agent_energetique_1",
    "unite_agent_energetique_1",
    "agent_energetique_2",
    "quantite_agent_energetique_2",
    "unite_agent_energetique_2",
    "agent_energetique_3",
    "quantite_agent_energetique_3",
    "unite_agent_energetique_3",
    "date_debut_periode",
    "date_fin_periode",
    "date_saisie",
    "indice_moy2",
    "annees_concernees_moy_2",
    "indice_moy3",
    "annees_concernees_moy_3",
    "id_concessionnaire",
    "nbre_preneur",
]


def fetch_idc_data(
    egid: Union[int, List[int]],
    url: str,
    fields: str = "*",
    chunk_size: int = 1000,
    table_name: str = "SCANE_INDICE_MOYENNES_3_ANS",
) -> Tuple[Optional[List[Dict]], Optional[List[Dict]]]:
    """
    Single API call replacing the previous two separate make_request() calls.

    Fetches with returnGeometry=true so both geometry and tabular data
    are retrieved in one round-trip, then splits the result.

    Returns:
        (geometry_records, data_records) — both None on error.
        geometry_records: list of {attributes, geometry} dicts for show_map.
        data_records:     cleaned, deduplicated attribute dicts for charts/tables.
    """
    where_clause = (
        f"egid IN ({','.join(map(str, egid))})"
        if isinstance(egid, list)
        else f"egid={egid}"
    )
    params = {
        "where": where_clause,
        "outFields": fields,
        "returnGeometry": "true",
        "f": "json",
        "resultOffset": 0,
        "resultRecordCount": chunk_size,
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if "features" not in data:
            logging.warning(f"{table_name} → 'features' not found in response")
            return None, None

        features = data["features"]

        # Geometry records: keep raw attributes + geometry for show_map
        geometry_records = [
            {"attributes": f["attributes"], "geometry": f["geometry"]} for f in features
        ]

        # Tabular records: clean and deduplicate with Polars
        raw_records = [f["attributes"] for f in features]
        df = (
            pl.from_dicts(raw_records)
            .select(RESULT_COLUMNS)
            .with_columns(
                [
                    pl.col("date_debut_periode").cast(pl.Datetime("ms")),
                    pl.col("date_fin_periode").cast(pl.Datetime("ms")),
                    pl.col("date_saisie").cast(pl.Datetime("ms")),
                    pl.col("npa").cast(pl.Int64),
                    pl.col("quantite_agent_energetique_1").cast(pl.Float64),
                    pl.col("quantite_agent_energetique_2").cast(pl.Float64),
                    pl.col("quantite_agent_energetique_3").cast(pl.Float64),
                ]
            )
            # Keep only the most recent saisie per (egid, annee)
            .sort(["egid", "annee", "date_saisie"], descending=[False, False, True])
            .unique(subset=["egid", "annee"], keep="first")
            .sort(["egid", "annee"])
        )

        return geometry_records, df.to_dicts()

    except requests.exceptions.RequestException as e:
        logging.error(f"{table_name} → Request error: {e}")
    except json.JSONDecodeError:
        logging.error(f"{table_name} → JSON decode error")

    return None, None


# ---------------------------------------------------------------------------
# Backward-compatible wrapper — kept for any other callers in the project
def make_request(
    offset: int,
    fields: str,
    url: str,
    chunk_size: int,
    table_name: str,
    geometry: bool,
    egid: Union[int, List[int]],
) -> Optional[List[Dict]]:
    """Legacy wrapper around fetch_idc_data(). Prefer fetch_idc_data() for new code."""
    geo, data = fetch_idc_data(egid, url, fields, chunk_size, table_name)
    return geo if geometry else data


# ---------------------------------------------------------------------------
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

        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": new_rings},
                "properties": item["attributes"],
            }
        )

    geojson = {"type": "FeatureCollection", "features": features}
    centroid = np.mean(all_points, axis=0)
    return geojson, centroid


# NOTE: @st.cache_data intentionally omitted — renders a Streamlit widget
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
    Columns are already ordered and deduplicated by fetch_idc_data().
    """
    df = pl.from_dicts(data)
    display_dataframe_with_excel_download(df.to_pandas())


def show_kpis(data_df: List[Dict], seuil: int = 450) -> None:
    """
    Display four KPI metrics above the chart:
      - Latest year IDC (SRE-weighted across all selected buildings)
      - 3-year rolling average (from API field indice_moy3, SRE-weighted)
      - Reference threshold (configurable via sidebar)
      - Compliance status

    SRE weighting ensures larger buildings are not treated equally to smaller
    ones when multiple EGIDs are selected.
    """
    df = pl.from_dicts(data_df).with_columns(
        [
            pl.col("sre").cast(pl.Float64),
            pl.col("indice").cast(pl.Float64),
            pl.col("indice_moy3").cast(pl.Float64),
        ]
    )

    latest_year = df["annee"].max()
    df_latest = df.filter(pl.col("annee") == latest_year)

    total_sre = df_latest["sre"].sum()

    if total_sre and total_sre > 0:
        idc_current = (df_latest["indice"] * df_latest["sre"]).sum() / total_sre

        df_moy3 = df_latest.filter(pl.col("indice_moy3").is_not_null())
        sre_moy3 = df_moy3["sre"].sum()
        idc_moy3 = (
            (df_moy3["indice_moy3"] * df_moy3["sre"]).sum() / sre_moy3
            if sre_moy3 and sre_moy3 > 0
            else None
        )
        idc_moy3_years = df_latest["annees_concernees_moy_3"].drop_nulls().to_list()
    else:
        # Fallback to simple mean when SRE is missing
        idc_current = df_latest["indice"].mean()
        idc_moy3_series = df_latest["indice_moy3"].drop_nulls()
        idc_moy3 = idc_moy3_series.mean() if len(idc_moy3_series) > 0 else None
        idc_moy3_years = "N/A"

    delta_abs = idc_current - seuil

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label=f"IDC ({latest_year})",
            value=f"{idc_current:.0f} MJ/m²",
            delta=f"{delta_abs:+.0f} MJ/m² vs seuil",
            # red when above threshold (inverse: positive delta = bad)
            delta_color="inverse",
        )
    with col2:
        st.metric(
            label=f"Moy. 3 ans ({', '.join(idc_moy3_years) if idc_moy3_years else 'N/A'})",
            value=f"{idc_moy3:.0f} MJ/m²" if idc_moy3 is not None else "N/A",
            help="Valeur indice_moy3 issue de la base SITG, pondérée par SRE.",
        )
    with col3:
        st.metric(
            label="Seuil de référence",
            value=f"{seuil} MJ/m²",
            help="Seuil indicatif configurable dans la barre latérale.",
        )


@st.cache_data
def create_barplot(
    data_df: List[Dict],
    nom_projet: str,
    seuil: Optional[int] = 450,
    year_range: Optional[Tuple[int, int]] = None,
) -> None:
    """
    Render a grouped bar chart of IDC by year and address.

    Improvements over original:
      - x-axis trimmed to actual data range (no trailing empty years)
      - year_range filter from sidebar
      - Horizontal reference line at configurable seuil
      - indice_moy3 overlay as a dashed line per building
      - Cross-join fill for missing years (no nested loops)
    """
    # Extra columns needed for the bar hover tooltip
    HOVER_COLS = [
        "sre",
        "destination",
        "agent_energetique_1",
        "quantite_agent_energetique_1",
        "unite_agent_energetique_1",
        "agent_energetique_2",
        "quantite_agent_energetique_2",
        "unite_agent_energetique_2",
        "agent_energetique_3",
        "quantite_agent_energetique_3",
        "unite_agent_energetique_3",
        "date_debut_periode",
        "date_fin_periode",
    ]
    df = pl.from_dicts(data_df).select(
        ["adresse", "egid", "annee", "indice", "indice_moy3", "annees_concernees_moy_3"]
        + HOVER_COLS
    )

    # Year bounds: trim to actual data, optionally narrowed by sidebar filter
    data_min = df["annee"].min()
    data_max = df["annee"].max()
    min_year = max(year_range[0], data_min) if year_range else data_min
    max_year = min(year_range[1], data_max) if year_range else data_max

    # Guard: if the selected period contains no data, show a warning and return early
    if min_year > max_year:
        st.warning(
            f"Aucune donnée disponible pour la période sélectionnée "
            f"({year_range[0]}–{year_range[1]}). "
            f"Les données couvrent {data_min}–{data_max}."
        )
        return

    # Explicit Int32 dtype prevents a Null-type schema when the range is empty
    years_df = pl.DataFrame(
        {"annee": pl.Series(range(min_year, max_year + 1), dtype=pl.Int32)}
    )

    # Ensure join key types match (API may return Int64; cast to Int32 for consistency)
    df = df.with_columns(pl.col("annee").cast(pl.Int32))

    # Cross-join all (adresse, egid) pairs with all years, then left-join data.
    # Hover columns are carried through so px.bar can reference them via custom_data.
    df_full = (
        df.select(["adresse", "egid"])
        .unique()
        .join(years_df, how="cross")
        .join(
            df.select(["adresse", "egid", "annee", "indice"] + HOVER_COLS),
            on=["adresse", "egid", "annee"],
            how="left",
        )
        .with_columns(pl.col("indice").fill_null(0))
        .sort(["annee", "adresse", "egid"])
        .with_columns(
            [
                (pl.col("adresse") + " - " + pl.col("egid").cast(pl.Utf8)).alias(
                    "adresse_egid"
                ),
                pl.when(pl.col("indice") > 0)
                .then(pl.col("indice").cast(pl.Int64).cast(pl.Utf8))
                .otherwise(pl.lit(""))
                .alias("text"),
                # Format agent lines: "Gaz — 257835 kWh" or empty when null
                pl.when(pl.col("agent_energetique_1").is_not_null())
                .then(
                    pl.col("agent_energetique_1")
                    + " — "
                    + pl.col("quantite_agent_energetique_1").cast(pl.Utf8)
                    + " "
                    + pl.col("unite_agent_energetique_1").fill_null("")
                )
                .otherwise(pl.lit(""))
                .alias("agent_1_label"),
                pl.when(pl.col("agent_energetique_2").is_not_null())
                .then(
                    pl.col("agent_energetique_2")
                    + " — "
                    + pl.col("quantite_agent_energetique_2").cast(pl.Utf8)
                    + " "
                    + pl.col("unite_agent_energetique_2").fill_null("")
                )
                .otherwise(pl.lit(""))
                .alias("agent_2_label"),
                pl.when(pl.col("agent_energetique_3").is_not_null())
                .then(
                    pl.col("agent_energetique_3")
                    + " — "
                    + pl.col("quantite_agent_energetique_3").cast(pl.Utf8)
                    + " "
                    + pl.col("unite_agent_energetique_3").fill_null("")
                )
                .otherwise(pl.lit(""))
                .alias("agent_3_label"),
                # Format period as "2014-05-01 → 2015-04-30"
                pl.col("date_debut_periode")
                .cast(pl.Utf8)
                .str.slice(0, 10)
                .alias("debut"),
                pl.col("date_fin_periode").cast(pl.Utf8).str.slice(0, 10).alias("fin"),
            ]
        )
    )

    # indice_moy3 series for the line overlay, filtered to selected year range
    # annees_concernees_moy_3 is included so it can be shown in the hover tooltip
    df_moy3 = (
        df.filter(
            (pl.col("annee") >= min_year)
            & (pl.col("annee") <= max_year)
            & pl.col("indice_moy3").is_not_null()
        )
        .with_columns(
            (pl.col("adresse") + " - " + pl.col("egid").cast(pl.Utf8)).alias(
                "adresse_egid"
            )
        )
        .select(["annee", "adresse_egid", "indice_moy3", "annees_concernees_moy_3"])
        .sort(["adresse_egid", "annee"])
    )

    longest_label = df_full["adresse_egid"].str.len_chars().max()
    right_margin = longest_label * 8 + 25

    # custom_data index mapping (used in hovertemplate):
    #   0: adresse_egid   1: sre   2: destination
    #   3: agent_1_label  4: agent_2_label  5: agent_3_label
    #   6: debut          7: fin
    fig = px.bar(
        df_full,
        x="annee",
        y="indice",
        color="adresse_egid",
        barmode="group",
        custom_data=[
            "adresse_egid",
            "sre",
            "destination",
            "agent_1_label",
            "agent_2_label",
            "agent_3_label",
            "debut",
            "fin",
        ],
        labels={
            "annee": "Année",
            "indice": "Indice [MJ/m²]",
            "adresse_egid": "Adresse - EGID",
        },
        title=f"Indice par Année et Adresse — {nom_projet}",
        text="text",
        height=450,
    )

    fig.update_traces(
        textposition="outside",
        texttemplate="%{text}",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Année : %{x}<br>"
            "IDC : <b>%{y:.0f} MJ/m²</b><br>"
            "SRE : %{customdata[1]:.0f} m²<br>"
            "Destination : %{customdata[2]}<br>"
            "Période : %{customdata[6]} → %{customdata[7]}<br>"
            "Agent 1 : %{customdata[3]}<br>"
            "Agent 2 : %{customdata[4]}<br>"
            "Agent 3 : %{customdata[5]}<br>"
            "<extra></extra>"
        ),
    )

    # Overlay indice_moy3 as a dashed line per building.
    # customdata carries annees_concernees_moy_3 so the hover shows which
    # years are included in the rolling average (e.g. "2018, 2019, 2020").
    palette = px.colors.qualitative.Plotly
    for i, group_df in enumerate(
        df_moy3.partition_by("adresse_egid", maintain_order=True)
    ):
        label = group_df["adresse_egid"][0]
        fig.add_trace(
            go.Scatter(
                x=group_df["annee"].to_list(),
                y=group_df["indice_moy3"].to_list(),
                mode="lines+markers",
                name=f"Moy3 — {label}",
                line=dict(dash="dash", color=palette[i % len(palette)], width=2),
                marker=dict(size=6),
                showlegend=True,
                # Pass the years string as custom hover data
                customdata=group_df["annees_concernees_moy_3"].to_list(),
                hovertemplate=(
                    "<b>Moy3</b>: %{y:.0f} MJ/m²<br>"
                    "<b>Années incluses</b>: %{customdata}<br>"
                    "<extra></extra>"
                ),
            )
        )

    # Reference line at IDC threshold
    if seuil is not None:
        fig.add_hline(
            y=seuil,
            line_dash="dot",
            line_color="red",
            line_width=1.5,
            annotation_text=f"Seuil {seuil} MJ/m²",
            annotation_position="top right",
            annotation_font_color="red",
        )

    y_max = max(df_full["indice"].max() or 0, seuil or 0) * 1.2

    fig.update_layout(
        xaxis_title="Année",
        yaxis_title="Indice [MJ/m²]",
        legend_title="Adresse - EGID",
        xaxis={
            "type": "category",
            "tickangle": 0,
            "gridcolor": "rgba(211, 211, 211, 0.2)",
            "tickfont": {"size": 12},
        },
        yaxis={
            "range": [0, y_max],
            "gridcolor": "rgba(211, 211, 211, 0.2)",
            "tickfont": {"size": 12},
        },
        margin=dict(t=50, r=right_margin, b=50, l=50),
        legend=dict(
            yanchor="top",
            y=1,
            xanchor="left",
            x=1,
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
                "zoom2d",
                "pan2d",
                "select2d",
                "lasso2d",
                "zoomIn2d",
                "zoomOut2d",
                "autoScale2d",
                "resetScale2d",
            ],
        },
    )


def refresh_adresses_db(
    url: str,
    db_path: str = "adresses_egid.db",
    chunk_size: int = 2000,
    max_workers: int = 8,
    progress_bar=None,
    status_text=None,
) -> int:
    """
    Fetch all unique address/EGID pairs from the SITG API and rebuild the
    local SQLite database from scratch.

    Performance strategy:
      - Fetch total count first, then compute all page offsets upfront.
      - Fetch all pages in parallel via ThreadPoolExecutor (default 8 workers).
      - Collect every record in memory, deduplicate with Polars, then do a
        single bulk INSERT — one transaction, no per-page commits.
      - chunk_size raised to 2000 (ArcGIS FeatureServer max) to halve the
        number of HTTP requests compared to 1000.

    Args:
        url:          SITG API endpoint (same URL used for IDC queries).
        db_path:      Path to the local SQLite database.
        chunk_size:   Records per API page (max 2000 for ArcGIS hosted services).
        max_workers:  Parallel HTTP threads. 8 is a safe ceiling for a public API.
        progress_bar: Optional st.progress placeholder for visual feedback.
        status_text:  Optional st.empty placeholder for status messages.

    Returns the total number of unique records saved.
    Cache invalidation is handled by the caller (get_all_addresses.clear()).
    """

    def _status(msg: str) -> None:
        if status_text is not None:
            status_text.caption(msg)
        logging.info(f"refresh_adresses_db → {msg}")

    def _progress(value: float) -> None:
        if progress_bar is not None:
            progress_bar.progress(value)

    # --- Step 1: total count so we can pre-compute all offsets ---
    _status("Connexion au SITG — récupération du nombre total d'adresses...")
    _progress(0.0)

    try:
        resp = requests.get(
            url, params={"where": "1=1", "returnCountOnly": "true", "f": "json"}
        )
        resp.raise_for_status()
        total_count = resp.json().get("count", 0)
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        logging.warning(f"refresh_adresses_db → count request failed: {e}")
        total_count = 0

    if total_count == 0:
        raise RuntimeError(
            "Impossible de récupérer le nombre total d'adresses depuis le SITG."
        )

    _status(f"{total_count:,} adresses trouvées — téléchargement en parallèle...")

    # Pre-compute every page offset so futures can be dispatched all at once
    offsets = list(range(0, total_count, chunk_size))
    completed_pages = 0
    lock = threading.Lock()
    all_records: list[tuple] = []

    # --- Step 2: fetch all pages in parallel ---
    def fetch_page(offset: int) -> list[tuple]:
        """Fetch one page and return list of (egid, adresse) tuples."""
        params = {
            "where": "1=1",
            "outFields": "adresse,egid",
            "returnGeometry": "false",
            "f": "json",
            "resultOffset": offset,
            "resultRecordCount": chunk_size,
        }
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        features = response.json().get("features", [])
        return [
            (f["attributes"]["egid"], f["attributes"]["adresse"])
            for f in features
            if f["attributes"].get("egid") and f["attributes"].get("adresse")
        ]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_page, off): off for off in offsets}
        for future in as_completed(futures):
            offset = futures[future]
            try:
                records = future.result()
            except Exception as e:
                raise RuntimeError(
                    f"Échec du téléchargement à l'offset {offset}: {e}"
                ) from e

            with lock:
                all_records.extend(records)
                completed_pages += 1
                progress_value = completed_pages / len(offsets)
                _progress(progress_value * 0.9)  # reserve last 10% for DB write
                _status(
                    f"Téléchargé {len(all_records):,} / ~{total_count:,} adresses "
                    f"({progress_value * 100:.0f}%)"
                )

    # --- Step 3: deduplicate with Polars before touching the DB ---
    _status("Dédoublonnage et écriture en base...")
    df = (
        pl.DataFrame(
            {
                "egid": [r[0] for r in all_records],
                "adresse": [r[1] for r in all_records],
            }
        )
        .unique()  # removes any cross-page duplicates the API may return
        .sort("adresse")
    )
    unique_records = df.rows()  # list of (egid, adresse) tuples

    # --- Step 4: rebuild table and bulk insert in one transaction ---
    # DROP + CREATE guarantees the PRIMARY KEY constraint is always present.
    conn = sqlite3.connect(db_path)
    conn.execute("DROP TABLE IF EXISTS adresses_egid")
    conn.execute("""
        CREATE TABLE adresses_egid (
            egid    INTEGER NOT NULL,
            adresse TEXT    NOT NULL,
            PRIMARY KEY (egid, adresse)
        )
    """)
    # Index on adresse speeds up ORDER BY in get_all_addresses()
    conn.execute("CREATE INDEX idx_adresse ON adresses_egid (adresse)")
    conn.execute("BEGIN")
    conn.executemany(
        "INSERT INTO adresses_egid (egid, adresse) VALUES (?, ?)",
        unique_records,
    )
    conn.execute("COMMIT")
    conn.close()

    _progress(1.0)
    _status(f"Terminé — {len(unique_records):,} adresses uniques enregistrées.")
    return len(unique_records)
