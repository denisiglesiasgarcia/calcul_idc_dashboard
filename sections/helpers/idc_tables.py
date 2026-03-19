# /sections/helpers/idc_tables.py

import logging
from typing import Dict, List, Optional, Tuple

import polars as pl
import streamlit as st

from sections.helpers.save_excel_streamlit import convert_df_to_excel

logging.basicConfig(level=logging.DEBUG)


def show_dataframe(
    data: List[Dict], seuil: int = 450, year_range: tuple = None
) -> None:
    st.subheader("Données IDC")
    df = pl.from_dicts(data)

    if year_range:
        df = df.filter(pl.col("annee").is_between(year_range[0], year_range[1]))

    # --- Detect which agent columns have actual data ---
    has_agent2 = df["agent_energetique_2"].drop_nulls().len() > 0
    has_agent3 = df["agent_energetique_3"].drop_nulls().len() > 0

    # --- Filter widgets: only show agents with data ---
    active_filters = st.columns(1 + has_agent2 + has_agent3)

    with active_filters[0]:
        agents1 = sorted(df["agent_energetique_1"].drop_nulls().unique().to_list())
        selected_a1 = st.multiselect(
            "Agent énergétique 1",
            options=agents1,
            default=agents1,
            key="df_filter_agent1",
        )

    selected_a2, selected_a3 = [], []

    if has_agent2:
        with active_filters[1]:
            agents2 = sorted(df["agent_energetique_2"].drop_nulls().unique().to_list())
            selected_a2 = st.multiselect(
                "Agent énergétique 2",
                options=agents2,
                default=agents2,
                key="df_filter_agent2",
            )

    if has_agent3:
        with active_filters[1 + has_agent2]:
            agents3 = sorted(df["agent_energetique_3"].drop_nulls().unique().to_list())
            selected_a3 = st.multiselect(
                "Agent énergétique 3",
                options=agents3,
                default=agents3,
                key="df_filter_agent3",
            )

    # Null-safe filter — agents without data are skipped entirely
    df_filtered = df.filter(
        pl.col("agent_energetique_1").is_in(selected_a1)
        & (
            pl.col("agent_energetique_2").is_null()
            | (
                pl.col("agent_energetique_2").is_in(selected_a2)
                if selected_a2
                else pl.lit(True)
            )
        )
        & (
            pl.col("agent_energetique_3").is_null()
            | (
                pl.col("agent_energetique_3").is_in(selected_a3)
                if selected_a3
                else pl.lit(True)
            )
        )
    )

    # --- Build visible columns dynamically based on available data ---
    base_cols = [
        "egid",
        "annee",
        "indice",
        "sre",
        "adresse",
        "agent_energetique_1",
        "quantite_agent_energetique_1",
        "unite_agent_energetique_1",
    ]
    if has_agent2:
        base_cols += [
            "agent_energetique_2",
            "quantite_agent_energetique_2",
            "unite_agent_energetique_2",
        ]
    if has_agent3:
        base_cols += [
            "agent_energetique_3",
            "quantite_agent_energetique_3",
            "unite_agent_energetique_3",
        ]
    base_cols += ["date_debut_periode", "date_fin_periode"]

    # --- Column visibility toggle ---
    show_all = st.checkbox(
        "Afficher toutes les colonnes", value=False, key="df_show_all"
    )
    cols_to_show = (
        df_filtered.columns
        if show_all
        else [c for c in base_cols if c in df_filtered.columns]
    )
    df_display = df_filtered.select(cols_to_show)

    # --- Summary row count ---
    st.caption(f"{len(df_filtered):,} ligne(s) affichée(s) sur {len(df):,}")

    # --- column_config: IDC as progress bar, dates formatted, SRE as number ---
    indice_max = int(df["indice"].drop_nulls().max() or 1000)

    col_cfg = {
        "indice": st.column_config.ProgressColumn(
            label="IDC [MJ/m²]",
            min_value=0,
            max_value=max(indice_max, seuil),
            format="%d MJ/m²",
        ),
        "sre": st.column_config.NumberColumn(label="SRE [m²]", format="%.0f m²"),
        "date_debut_periode": st.column_config.DateColumn(
            label="Début période", format="DD.MM.YYYY"
        ),
        "date_fin_periode": st.column_config.DateColumn(
            label="Fin période", format="DD.MM.YYYY"
        ),
        "date_saisie": st.column_config.DateColumn(
            label="Date saisie", format="DD.MM.YYYY"
        ),
        "annee": st.column_config.NumberColumn(label="Année", format="%d"),
        "indice_moy3": st.column_config.NumberColumn(
            label="IDC moy. 3 ans", format="%.0f MJ/m²"
        ),
        "quantite_agent_energetique_1": st.column_config.NumberColumn(
            label="Qté agent 1", format="%.0f"
        ),
        "quantite_agent_energetique_2": st.column_config.NumberColumn(
            label="Qté agent 2", format="%.0f"
        ),
        "quantite_agent_energetique_3": st.column_config.NumberColumn(
            label="Qté agent 3", format="%.0f"
        ),
    }

    # --- Highlight rows above seuil via pandas styler ---
    df_pd = df_display.to_pandas()

    def highlight_seuil(row):
        """Red background only when IDC exceeds seuil and seuil is non-zero."""
        if seuil > 0 and "indice" in row.index and row["indice"] > seuil:
            return ["background-color: #fdd" for _ in row]
        return ["" for _ in row]

    styled = df_pd.style.apply(highlight_seuil, axis=1)

    st.dataframe(
        styled,
        column_config=col_cfg,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        label="📥 Télécharger idc_data.xlsx",
        data=convert_df_to_excel(df_pd),
        file_name="idc_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=False,
    )

    _show_groupby_annee(df_filtered, seuil)

    st.subheader("Agents énergétiques par année")
    show_energy_agents_table(data, year_range=year_range)

    st.subheader("Surface de référence (SRE) par année")
    show_sre_table(data, year_range=year_range)


def _show_groupby_annee(df_display: pl.DataFrame, seuil: int) -> None:
    """
    Second table — SRE-weighted IDC aggregated by year across all selected buildings.
    Only shown when multiple EGIDs are present in the filtered data.
    """
    n_egids = df_display["egid"].n_unique()
    if n_egids < 2:
        return

    st.subheader("IDC pondéré par année (agrégation de tous les bâtiments sélectionnés)")
    st.caption(f"Agrégation de {n_egids} bâtiments — pondération par surface SRE")

    df_grouped = (
        df_display.with_columns(
            [
                pl.col("sre").cast(pl.Float64),
                pl.col("indice").cast(pl.Float64),
            ]
        )
        .group_by("annee")
        .agg(
            [
                (pl.col("indice") * pl.col("sre")).sum().alias("_indice_x_sre"),
                pl.col("sre").sum().alias("sre_totale"),
                pl.col("indice").min().alias("indice_min"),
                pl.col("indice").max().alias("indice_max"),
                pl.col("egid").n_unique().alias("n_batiments"),
            ]
        )
        .with_columns(
            (pl.col("_indice_x_sre") / pl.col("sre_totale"))
            .round(0)
            .cast(pl.Int64)
            .alias("indice_pondere")
        )
        .drop("_indice_x_sre")
        .sort("annee")
        .with_columns(
            pl.col("indice_pondere")
            .cast(pl.Float64)
            .rolling_mean(window_size=3, min_periods=3)
            .round(0)
            .cast(pl.Int64)
            .alias("indice_moy3_calcule")
        )
        .with_columns(
            [
                # Retrieve the 2 preceding years for the label
                pl.col("annee").shift(2).alias("_y2"),
                pl.col("annee").shift(1).alias("_y1"),
            ]
        )
        .with_columns(
            # Only populate when rolling mean is valid (3 years available)
            pl.when(pl.col("indice_moy3_calcule").is_not_null())
            .then(
                pl.col("_y2").cast(pl.Utf8)
                + ", "
                + pl.col("_y1").cast(pl.Utf8)
                + ", "
                + pl.col("annee").cast(pl.Utf8)
            )
            .otherwise(pl.lit(None))
            .alias("annees_concernees_moy3_calcule")
        )
        .drop(["_y2", "_y1"])
        # Delta year-over-year — nul pour la première ligne
        .with_columns(
            pl.col("indice_pondere")
            .cast(pl.Float64)
            .diff()
            .round(0)
            .cast(pl.Int64)
            .alias("delta_annuel")
        )
    )

    indice_max = int(df_grouped["indice_pondere"].max() or 1000)

    col_cfg = {
        "annee": st.column_config.NumberColumn(label="Année", format="%d"),
        "indice_pondere": st.column_config.ProgressColumn(
            label="IDC pondéré [MJ/m²]",
            min_value=0,
            max_value=max(indice_max, seuil),
            format="%d MJ/m²",
        ),
        "sre_totale": st.column_config.NumberColumn(
            label="SRE totale [m²]", format="%.0f m²"
        ),
        "indice_min": st.column_config.NumberColumn(
            label="IDC min [MJ/m²]", format="%d"
        ),
        "indice_max": st.column_config.NumberColumn(
            label="IDC max [MJ/m²]", format="%d"
        ),
        "n_batiments": st.column_config.NumberColumn(label="Nb bâtiments", format="%d"),
        "indice_moy3_calcule": st.column_config.NumberColumn(
            label="Moy. 3 ans [MJ/m²]",
            format="%d MJ/m²",
            help="Moyenne pondérée SRE sur 3 ans. Null si moins de 3 ans disponibles.",
        ),
        "annees_concernees_moy3_calcule": st.column_config.TextColumn(
            label="Années moy. 3 ans",
            help="Les 3 années incluses dans le calcul de la moyenne glissante.",
        ),
        "delta_annuel": st.column_config.NumberColumn(
            label="Δ annuel [MJ/m²]",
            format="%+d MJ/m²",
            help="Variation year-over-year de l'IDC pondéré SRE. Nul pour la première année disponible.",
        ),
    }

    st.dataframe(
        df_grouped.to_pandas(),
        column_config=col_cfg,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        label="📥 Télécharger idc_grouped_by_year.xlsx",
        data=convert_df_to_excel(df_grouped.to_pandas()),
        file_name="idc_grouped_by_year.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=False,
    )


def show_energy_agents_table(
    data: List[Dict],
    year_range: Optional[Tuple[int, int]] = None,
) -> None:
    """
    Affiche une matrice année × bâtiment montrant l'agent énergétique principal.
    Permet de détecter rapidement les changements de vecteur énergétique.
    """
    df = pl.from_dicts(data)

    if year_range:
        df = df.filter(pl.col("annee").is_between(year_range[0], year_range[1]))

    df = df.with_columns(
        (pl.col("adresse") + " - " + pl.col("egid").cast(pl.Utf8)).alias("adresse_egid")
    ).select(["adresse_egid", "annee", "agent_energetique_1"])

    # Pivot : lignes = bâtiment, colonnes = année
    df_pivot = df.pivot(
        index="adresse_egid", on="annee", values="agent_energetique_1"
    ).sort("adresse_egid")

    # Colonnes année triées chronologiquement
    year_cols = sorted(
        [c for c in df_pivot.columns if c != "adresse_egid"],
        key=lambda x: int(x),
    )
    df_pivot = df_pivot.select(["adresse_egid"] + year_cols)

    st.caption(
        "Agent énergétique principal (agent_energetique_1) par année. "
        "Une cellule vide indique absence de données pour cette année."
    )
    st.dataframe(df_pivot, use_container_width=True, hide_index=True)

def show_sre_table(
    data: List[Dict],
    year_range: Optional[Tuple[int, int]] = None,
) -> None:
    """
    Affiche une matrice année × bâtiment montrant la surface de référence (SRE).
    Permet de détecter rapidement les changements de vecteur énergétique.
    """
    df = pl.from_dicts(data)

    if year_range:
        df = df.filter(pl.col("annee").is_between(year_range[0], year_range[1]))

    df = df.with_columns(
        (pl.col("adresse") + " - " + pl.col("egid").cast(pl.Utf8)).alias("adresse_egid")
    ).select(["adresse_egid", "annee", "sre"])

    # Pivot : lignes = bâtiment, colonnes = année
    df_pivot = df.pivot(
        index="adresse_egid", on="annee", values="sre"
    ).sort("adresse_egid")

    # Colonnes année triées chronologiquement
    year_cols = sorted(
        [c for c in df_pivot.columns if c != "adresse_egid"],
        key=lambda x: int(x),
    )
    df_pivot = df_pivot.select(["adresse_egid"] + year_cols)

    st.caption(
        "Surface de référence (SRE) par année. "
        "Une cellule vide indique absence de données pour cette année."
    )
    st.dataframe(df_pivot, use_container_width=True, hide_index=True)


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

    if seuil > 0:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label=f"IDC pondéré ({latest_year})",
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
    elif seuil == 0:
        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                label=f"IDC pondéré ({latest_year})",
                value=f"{idc_current:.0f} MJ/m²",
            )
        with col2:
            st.metric(
                label=f"Moy. 3 ans ({', '.join(idc_moy3_years) if idc_moy3_years else 'N/A'})",
                value=f"{idc_moy3:.0f} MJ/m²" if idc_moy3 is not None else "N/A",
                help="Valeur indice_moy3 issue de la base SITG, pondérée par SRE.",
            )
