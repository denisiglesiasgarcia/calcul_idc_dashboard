# /sections/helpers/idc_charts.py

import logging
from typing import Dict, List, Optional, Tuple

import plotly.express as px
import plotly.graph_objects as go
import polars as pl
import streamlit as st


logging.basicConfig(level=logging.WARNING)


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
                # Agent 1
                pl.when(pl.col("agent_energetique_1").is_not_null())
                .then(
                    pl.col("agent_energetique_1")
                    + " — "
                    + pl.col("quantite_agent_energetique_1")
                    .cast(pl.Float64)
                    .round(0)
                    .cast(pl.Int64)
                    .cast(pl.Utf8)
                    + " "
                    + pl.col("unite_agent_energetique_1").fill_null("")
                )
                .otherwise(pl.lit(""))
                .alias("agent_1_label"),
                # Agent 2
                pl.when(pl.col("agent_energetique_2").is_not_null())
                .then(
                    pl.col("agent_energetique_2")
                    + " — "
                    + pl.col("quantite_agent_energetique_2")
                    .cast(pl.Float64)
                    .round(0)
                    .cast(pl.Int64)
                    .cast(pl.Utf8)
                    + " "
                    + pl.col("unite_agent_energetique_2").fill_null("")
                )
                .otherwise(pl.lit(""))
                .alias("agent_2_label"),
                # Agent 3
                pl.when(pl.col("agent_energetique_3").is_not_null())
                .then(
                    pl.col("agent_energetique_3")
                    + " — "
                    + pl.col("quantite_agent_energetique_3")
                    .cast(pl.Float64)
                    .round(0)
                    .cast(pl.Int64)
                    .cast(pl.Utf8)
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
    n_egids = df["egid"].n_unique()
    barmode = "relative" if n_egids == 1 else "group"
    height = max(450, n_egids * 60 + 200)
    fig = px.bar(
        df_full,
        x="annee",
        y="indice",
        color="adresse_egid",
        barmode=barmode,
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
        height=height,
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
                x=group_df["annee"].cast(pl.Utf8).to_list(),
                y=group_df["indice_moy3"].to_list(),
                mode="lines+markers",
                name=f"Moy3 — {label}",
                line=dict(dash="dash", color=palette[i % len(palette)], width=1),
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

    # --- IDC pondéré agrégé (uniquement si plusieurs EGIDs) ---
    if n_egids >= 2:
        df_pondere = (
            df.filter((pl.col("annee") >= min_year) & (pl.col("annee") <= max_year))
            .with_columns(
                [
                    pl.col("sre").cast(pl.Float64),
                    pl.col("indice").cast(pl.Float64),
                ]
            )
            .group_by("annee")
            .agg(
                [
                    (pl.col("indice") * pl.col("sre")).sum().alias("_indice_x_sre"),
                    pl.col("sre").sum().alias("_sre_total"),
                ]
            )
            .with_columns(
                (pl.col("_indice_x_sre") / pl.col("_sre_total"))
                .round(0)
                .alias("indice_pondere")
            )
            .drop(["_indice_x_sre", "_sre_total"])
            .sort("annee")
            .with_columns(
                pl.col("indice_pondere")
                .cast(pl.Float64)
                .rolling_mean(window_size=3, min_periods=3)
                .round(0)
                .alias("indice_pondere_moy3")
            )
            # Construire le label des 3 années incluses dans la moyenne glissante
            .with_columns(
                [
                    pl.col("annee").shift(2).alias("_y2"),
                    pl.col("annee").shift(1).alias("_y1"),
                ]
            )
            .with_columns(
                pl.when(pl.col("indice_pondere_moy3").is_not_null())
                .then(
                    pl.col("_y2").cast(pl.Utf8)
                    + ", "
                    + pl.col("_y1").cast(pl.Utf8)
                    + ", "
                    + pl.col("annee").cast(pl.Utf8)
                )
                .otherwise(pl.lit(None))
                .alias("annees_moy3_label")
            )
            .drop(["_y2", "_y1"])
        )

        fig.add_trace(
            go.Scatter(
                x=df_pondere["annee"].cast(pl.Utf8).to_list(),
                y=df_pondere["indice_pondere"].to_list(),
                mode="lines+markers",
                name="IDC pondéré ∑(SRE x IDC)/∑SRE",
                line=dict(dash="dash", color="black", width=1),
                marker=dict(size=6, symbol="diamond", color="black"),
                showlegend=True,
                hovertemplate=(
                    "<b>IDC pondéré SRE</b><br>"
                    "Année : %{x}<br>"
                    "IDC agrégé : <b>%{y:.0f} MJ/m²</b><br>"
                    "<extra></extra>"
                ),
            )
        )

        # Trace moy3 agrégée — uniquement les années où 3 valeurs sont disponibles
        df_moy3_pondere = df_pondere.filter(pl.col("indice_pondere_moy3").is_not_null())
        if len(df_moy3_pondere) > 0:
            fig.add_trace(
                go.Scatter(
                    x=df_moy3_pondere["annee"].cast(pl.Utf8).to_list(),
                    y=df_moy3_pondere["indice_pondere_moy3"].to_list(),
                    mode="lines+markers",
                    name="Moy3 pondérée ∑(SRE x IDC)/∑SRE",
                    line=dict(dash="dot", color="grey", width=1),
                    marker=dict(size=5, symbol="diamond", color="grey"),
                    showlegend=True,
                    customdata=df_moy3_pondere["annees_moy3_label"].to_list(),
                    hovertemplate=(
                        "<b>Moy3 pondérée SRE (agrégé)</b><br>"
                        "Année : %{x}<br>"
                        "IDC moy3 agrégé : <b>%{y:.0f} MJ/m²</b><br>"
                        "Années incluses : %{customdata}<br>"
                        "<extra></extra>"
                    ),
                )
            )

    # Reference line at IDC threshold
    if seuil:
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
