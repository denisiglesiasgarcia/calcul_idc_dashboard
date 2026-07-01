# /sections/helpers/idc_tables.py

import logging
from typing import Optional, cast

import pandas as pd
import polars as pl
import streamlit as st

from sections.helpers.save_excel_streamlit import convert_df_to_excel

logging.basicConfig(level=logging.WARNING)


def show_dataframe(
    data: list[dict], seuil: int = 450, year_range: Optional[tuple] = None
) -> None:
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
    indice_max = int(cast(int, df["indice"].drop_nulls().max()) or 1000)

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

    def _highlight_seuil_col(col_series):
        if seuil <= 0 or "indice" not in df_pd.columns:
            return [""] * len(col_series)
        mask = df_pd["indice"] > seuil
        return ["background-color: #fdd" if v else "" for v in mask]

    styled = df_pd.style.apply(_highlight_seuil_col)

    st.dataframe(
        styled,
        column_config=col_cfg,
        width="stretch",
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

    st.subheader(
        "IDC pondéré par année (agrégation de tous les bâtiments sélectionnés)"
    )
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
            .rolling_mean(window_size=3, min_samples=3)
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

    indice_max = int(cast(int, df_grouped["indice_pondere"].max()) or 1000)

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
            help=(
                "Variation year-over-year de l'IDC pondéré SRE. "
                "Nul pour la première année disponible."
            ),
        ),
    }

    df_pd = df_grouped.to_pandas()

    def _style_delta(val):
        """Couleur texte sur delta_annuel : vert si baisse (amélioration),
        rouge si hausse."""
        if pd.isna(val) or val == 0:
            return ""
        return (
            "color: #28a745; font-weight: bold"
            if val < 0
            else "color: #dc3545; font-weight: bold"
        )

    styled = df_pd.style.map(_style_delta, subset=["delta_annuel"])

    st.dataframe(
        styled,
        column_config=col_cfg,
        width="stretch",
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
    data: list[dict],
    year_range: tuple[int, int] | None = None,
) -> None:
    """
    Affiche une matrice année × bâtiment montrant les agents énergétiques.
    Les agents 1/2/3 sont concaténés dans la cellule si plusieurs existent.
    Permet de détecter rapidement les changements de vecteur énergétique.
    """
    df = pl.from_dicts(data)

    if year_range:
        df = df.filter(pl.col("annee").is_between(year_range[0], year_range[1]))

    # Colonnes agents présentes dans le dataset (1 est obligatoire, 2 et 3 optionnelles)
    agent_cols = [
        c
        for c in ["agent_energetique_1", "agent_energetique_2", "agent_energetique_3"]
        if c in df.columns
    ]

    # Cast tous les agents en Utf8 et remplace les nulls par "" pour la concaténation
    df = df.with_columns([pl.col(c).cast(pl.Utf8).fill_null("") for c in agent_cols])

    # Concatène les agents non-vides séparés par " / "
    df = df.with_columns(
        pl.concat_str(
            [pl.col(c) for c in agent_cols],
            separator=" / ",
            ignore_nulls=True,
        )
        # Supprime les " / " en fin de chaîne laissés par les agents vides
        .str.replace_all(r"(?: / )+$", "")
        .str.replace_all(r"^ / | / $", "")
        .str.replace_all(r" /  / ", " / ")
        .alias("agents")
    )

    df = df.with_columns(
        (pl.col("adresse") + " - " + pl.col("egid").cast(pl.Utf8)).alias("adresse_egid")
    )

    # Pivot : lignes = bâtiment, colonnes = année
    df_pivot = df.pivot(index="adresse_egid", on="annee", values="agents").sort(
        "adresse_egid"
    )

    # Colonnes année triées chronologiquement
    year_cols = sorted(
        [c for c in df_pivot.columns if c != "adresse_egid"],
        key=lambda x: int(x),
    )
    df_pivot = df_pivot.select(["adresse_egid"] + year_cols)

    st.caption(
        f"Agents énergétiques ({', '.join(agent_cols)}) concaténés par année. "
        "Une cellule vide indique absence de données."
    )
    df_pd = df_pivot.to_pandas()

    def _highlight_agent_changes(df: pd.DataFrame) -> pd.DataFrame:
        """
        Surligne les cellules où l'agent diffère de l'année précédente.
        Ignore les transitions depuis/vers NaN (absence de données).
        """
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        for i in range(1, len(year_cols)):
            prev, curr = year_cols[i - 1], year_cols[i]
            if prev not in df.columns or curr not in df.columns:
                continue
            changed = df[curr].notna() & df[prev].notna() & (df[curr] != df[prev])
            styles.loc[changed, curr] = "background-color: #fff3cd; font-weight: bold"
        return styles

    styled = df_pd.style.apply(_highlight_agent_changes, axis=None)
    st.dataframe(styled, width="stretch", hide_index=True)


def show_sre_table(
    data: list[dict],
    year_range: tuple[int, int] | None = None,
) -> None:
    """
    Affiche une matrice année × bâtiment montrant la surface de référence (SRE).
    Permet de détecter rapidement les changements de vecteur énergétique.
    """
    df = pl.from_dicts(data)

    if year_range:
        df = df.filter(pl.col("annee").is_between(year_range[0], year_range[1]))

    df = df.with_columns(
        (pl.col("adresse") + " - " + pl.col("egid").cast(pl.Utf8)).alias(
            "adresse_egid"
        ),
        pl.col("sre").cast(pl.Int64),  # int pour tous
    ).select(["adresse_egid", "annee", "sre"])

    # Pivot : lignes = bâtiment, colonnes = année
    df_pivot = df.pivot(index="adresse_egid", on="annee", values="sre").sort(
        "adresse_egid"
    )

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

    df_pd = df_pivot.to_pandas()

    def _highlight_sre_changes(df: pd.DataFrame) -> pd.DataFrame:
        """
        Surligne les cellules où la SRE diffère de l'année précédente (tolérance 1 m²).
        Conversion en float pour éviter les problèmes avec les entiers nullable
        pandas (Int64/pd.NA).
        """
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        df_float = df[year_cols].astype("float")
        for i in range(1, len(year_cols)):
            prev, curr = year_cols[i - 1], year_cols[i]
            if prev not in df.columns or curr not in df.columns:
                continue
            prev_f = df_float[prev]
            curr_f = df_float[curr]
            changed = curr_f.notna() & prev_f.notna() & ((curr_f - prev_f).abs() > 1)
            styles.loc[changed, curr] = "background-color: #fff3cd; font-weight: bold"
        return styles

    styled = (
        df_pd.style.apply(_highlight_sre_changes, axis=None)
        # Affiche les entiers sans décimales, cellule vide si null
        .format(lambda x: f"{int(x)}" if pd.notna(x) else "", subset=year_cols)
    )
    st.dataframe(styled, width="stretch", hide_index=True)


def show_kpis(
    data_df: list[dict],
    seuil: int = 450,
    year_range: tuple[int, int] | None = None,
    autor_records: list[dict] | None = None,
    batiment_records: list[dict] | None = None,
) -> None:

    df = pl.from_dicts(data_df).with_columns(
        [
            pl.col("sre").cast(pl.Float64),
            pl.col("indice").cast(pl.Float64),
        ]
    )

    # Respect du slider — filtre avant tout calcul
    if year_range:
        df = df.filter(pl.col("annee").is_between(year_range[0], year_range[1]))

    latest_year = int(cast(int, df["annee"].max()))
    first_year = int(cast(int, df["annee"].min()))
    df_latest = df.filter(pl.col("annee") == latest_year)
    total_sre = cast(float, df_latest["sre"].sum())

    # IDC pondéré SRE dernière année
    if total_sre and total_sre > 0:
        indice_x_sre = cast(float, (df_latest["indice"] * df_latest["sre"]).sum())
        idc_current = indice_x_sre / total_sre
    else:
        idc_current = cast(float, df_latest["indice"].mean())

    # Agrégation annuelle pondérée SRE
    df_agg = (
        df.group_by("annee")
        .agg(
            [
                (pl.col("indice") * pl.col("sre")).sum().alias("_indice_x_sre"),
                pl.col("sre").sum().alias("_sre_total"),
                pl.col("indice").mean().alias("_indice_mean"),
            ]
        )
        .with_columns(
            pl.when(pl.col("_sre_total") > 0)
            .then(pl.col("_indice_x_sre") / pl.col("_sre_total"))
            .otherwise(pl.col("_indice_mean"))
            .round(0)
            .alias("indice_pondere")
        )
        .drop(["_indice_x_sre", "_sre_total", "_indice_mean"])
        .sort("annee")
        .with_columns(
            pl.col("indice_pondere")
            .cast(pl.Float64)
            .rolling_mean(window_size=3, min_samples=3)
            .round(0)
            .alias("indice_pondere_moy3")
        )
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

    # Moy3 dernière valeur disponible
    df_moy3_valid = df_agg.filter(pl.col("indice_pondere_moy3").is_not_null())
    if len(df_moy3_valid) > 0:
        last_row = df_moy3_valid.tail(1)
        idc_moy3 = last_row["indice_pondere_moy3"][0]
        idc_moy3_label = last_row["annees_moy3_label"][0]
    else:
        idc_moy3 = None
        idc_moy3_label = None

    # Ratio première → dernière année
    df_first = df.filter(pl.col("annee") == first_year)
    sre_first = cast(float, df_first["sre"].sum())
    idc_first = (
        cast(float, (df_first["indice"] * df_first["sre"]).sum()) / sre_first
        if sre_first and sre_first > 0
        else cast(float, df_first["indice"].mean())
    )
    ratio = (
        ((idc_current - idc_first) / idc_first * 100)
        if idc_first and idc_first > 0
        else None
    )

    # Années manquantes dans la plage (utilise les bornes du slider si disponibles)
    range_start = year_range[0] if year_range else first_year
    range_end = year_range[1] if year_range else latest_year
    all_years = set(range(range_start, range_end + 1))
    years_with_data = set(df["annee"].unique().to_list())
    missing_years = sorted(all_years - years_with_data)
    n_missing = len(missing_years)
    missing_label = (
        ", ".join(str(y) for y in missing_years) if missing_years else "Aucune"
    )

    # Changement agent énergétique par EGID
    df_agents = (
        df.filter(pl.col("annee").is_in([first_year, latest_year]))
        .group_by(["egid", "annee"])
        .agg(pl.col("agent_energetique_1").first())
        .sort(["egid", "annee"])
    )
    df_agent_pivot = df_agents.pivot(
        index="egid", on="annee", values="agent_energetique_1"
    )
    first_col, last_col = str(first_year), str(latest_year)
    if first_col in df_agent_pivot.columns and last_col in df_agent_pivot.columns:
        changed = df_agent_pivot.filter(
            pl.col(first_col).is_not_null()
            & pl.col(last_col).is_not_null()
            & (pl.col(first_col) != pl.col(last_col))
        )
        n_changed = len(changed)
        n_egids_total = df["egid"].n_unique()
        agent_value = f"{n_changed}/{n_egids_total}" if n_changed > 0 else "Aucun"
    else:
        agent_value = "N/A"
        n_changed = 0

    # Variation SRE — utilise les années où tous les bâtiments ont une SRE valide
    n_egids_sre = df["egid"].n_unique()
    df_sre_coverage = (
        df.filter(pl.col("sre").is_not_null() & (pl.col("sre") > 0))
        .group_by("annee")
        .agg(pl.col("egid").n_unique().alias("n_egids_with_sre"))
        .filter(pl.col("n_egids_with_sre") == n_egids_sre)
        .sort("annee")
    )
    if not df_sre_coverage.is_empty():
        sre_year_first = int(cast(int, df_sre_coverage["annee"].min()))
        sre_year_last = int(cast(int, df_sre_coverage["annee"].max()))
        sre_val_first = cast(
            float, df.filter(pl.col("annee") == sre_year_first)["sre"].sum()
        )
        sre_val_last = cast(
            float, df.filter(pl.col("annee") == sre_year_last)["sre"].sum()
        )
        if sre_val_first and sre_val_first > 0 and sre_val_last and sre_val_last > 0:
            sre_delta = sre_val_last - sre_val_first
        else:
            sre_delta = None
    else:
        sre_year_first = first_year
        sre_year_last = latest_year
        sre_val_first = sre_first
        sre_val_last = cast(float, df_latest["sre"].sum())
        if sre_val_first and sre_val_first > 0 and sre_val_last and sre_val_last > 0:
            sre_delta = sre_val_last - sre_val_first
        else:
            sre_delta = None

    # Variation absolue IDC vs seuil
    delta_abs = idc_current - seuil

    # ── Ligne 1 : IDC / moy3 / seuil ──────────────────────────────────────────
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    if seuil > 0:
        with col1:
            st.metric(
                label=f"Dernier IDC pondéré ({latest_year})",
                value=f"{idc_current:.0f} MJ/m²",
                delta=f"{delta_abs:+.0f} MJ/m² vs seuil",
                delta_color="inverse",
            )
    elif seuil == 0:
        with col1:
            st.metric(
                label="Dernier IDC pondéré",
                value=f"{idc_current:.0f} MJ/m²",
                delta=f"{latest_year}" if latest_year is not None else "",
                delta_color="off",
                delta_arrow="off",
                help="IDC pondéré par SRE pour la dernière année disponible.",
            )
    with col2:
        st.metric(
            label="Dernier IDC moy. 3 ans",
            value=f"{idc_moy3:.0f} MJ/m²" if idc_moy3 is not None else "N/A",
            delta=f"{idc_moy3_label}" if idc_moy3_label else "",
            delta_color="off",
            delta_arrow="off",
            help="Moyenne pondérée SRE sur 3 ans glissants.",
        )
    with col3:
        arrow_col3 = "down" if idc_current < idc_first else "up"
        st.metric(
            label=f"Évolution IDC ({first_year}→{latest_year})",
            value=f"{ratio:+.1f} %" if ratio is not None else "N/A",
            delta=f"{idc_first:.0f} → {idc_current:.0f} MJ/m²"
            if idc_first is not None
            else None,
            delta_arrow=arrow_col3,
            help=(
                "Variation relative de l'IDC pondéré entre "
                "première et dernière année de la période."
            ),
        )
    with col4:
        st.metric(
            label="Années sans données",
            value=str(n_missing) if n_missing > 0 else "Aucune",
            delta=f"{missing_label}" if n_missing > 0 else "",
            delta_color="off",
            delta_arrow="off",
            help=f"Années manquantes dans la plage sélectionnée : {missing_label}",
        )
    with col5:
        st.metric(
            label=f"Changement agent ({first_year}→{latest_year})",
            value=agent_value,
            help=(
                "Bâtiments dont l'agent énergétique principal a changé sur la période."
            ),
        )
    with col6:
        arrow_col6 = (
            "down"
            if sre_delta is not None and sre_delta < 0
            else "off"
            if sre_delta == 0
            else "up"
        )
        st.metric(
            label=f"Variation SRE ({sre_year_first}→{sre_year_last})",
            value=f"{sre_delta:+.0f} m²"
            if sre_delta != 0 and sre_delta is not None
            else "Aucune"
            if sre_delta == 0
            else "",
            delta=f"{sre_val_first:+.0f} → {sre_val_last:+.0f} m²"
            if sre_delta != 0 and sre_val_first is not None and sre_val_last is not None
            else "",
            delta_arrow=arrow_col6,
            help=(
                "Variation de la SRE totale entre la première et la dernière année "
                "où tous les bâtiments ont une SRE. Si aucune telle année n'existe, "
                "la première et la dernière année de la période sont utilisées."
            ),
        )

    # ── Ligne 2 : Dossiers d'autorisation ─────────────────────────────────────
    if autor_records is not None:
        n_autor_total = len(autor_records)
        n_agr = sum(1 for r in autor_records if r.get("type_operation") == "AGR")
        col_a1, col_a2, *_ = st.columns(6)
        with col_a1:
            st.metric(
                label="Dossiers d'autorisation",
                value=str(n_autor_total) if n_autor_total > 0 else "Aucun",
                help="Nombre total de dossiers d'autorisation liés aux bâtiments sélectionnés.",
            )
        with col_a2:
            st.metric(
                label='Opérations "AGR"',
                value=str(n_agr) if n_agr > 0 else "Aucune",
                help='Dossiers dont le type d\'opération est "AGR".',
            )

    # ── Ligne 3 : Caractéristiques des bâtiments (CAD_BATIMENT_HORSOL) ─────────
    if batiment_records:
        _show_batiment_kpis(batiment_records)


def _show_batiment_kpis(batiment_records: list[dict]) -> None:
    """
    KPI row summarising the building characteristics layer for the selected EGIDs.

    Destination and construction period are the attributes most relevant to an IDC
    reading (building use and age strongly shape expected heat demand); total
    footprint gives the physical scale of the selection.
    """
    # Destination — predominant use, with the full set of distinct uses in help.
    destinations = [
        r.get("destination") for r in batiment_records if r.get("destination")
    ]
    distinct_dest = sorted(set(destinations))
    if not distinct_dest:
        dest_value, dest_help = "N/A", "Destination non renseignée."
    elif len(distinct_dest) == 1:
        dest_value, dest_help = (
            distinct_dest[0],
            "Destination des bâtiments sélectionnés.",
        )
    else:
        # Most frequent destination as the headline, full list in the tooltip.
        predominant = max(distinct_dest, key=destinations.count)
        dest_value = f"{predominant} (+{len(distinct_dest) - 1})"
        dest_help = "Destinations présentes : " + ", ".join(distinct_dest)

    # Construction period — year range, falling back to the textual epoch.
    annees = [
        r.get("annee_construction")
        for r in batiment_records
        if r.get("annee_construction")
    ]
    if annees:
        a_min, a_max = min(annees), max(annees)
        constr_value = str(a_min) if a_min == a_max else f"{a_min}–{a_max}"
        constr_help = "Année de construction (min–max des bâtiments sélectionnés)."
    else:
        epoques = sorted(
            {
                r.get("epoque_construction")
                for r in batiment_records
                if r.get("epoque_construction")
            }
        )
        if not epoques:
            constr_value, constr_help = "N/A", "Année de construction non renseignée."
        elif len(epoques) == 1:
            constr_value, constr_help = epoques[0], "Époque de construction."
        else:
            constr_value = f"{len(epoques)} époques"
            constr_help = "Époques présentes : " + ", ".join(epoques)

    # Total ground footprint (m²) — physical extent of the selection.
    surfaces = [r.get("surface") for r in batiment_records if r.get("surface")]
    emprise = sum(surfaces) if surfaces else None
    emprise_value = f"{emprise:,.0f} m²".replace(",", "'") if emprise else "N/A"

    def _range_value(key: str, unit: str = "", decimals: int = 0) -> str:
        """Format the min–max of a numeric building attribute over the selection."""
        vals = [r.get(key) for r in batiment_records if r.get(key) is not None]
        if not vals:
            return "N/A"
        lo, hi = min(vals), max(vals)
        fmt = f"{{:.{decimals}f}}"
        suffix = f" {unit}" if unit else ""
        if lo == hi:
            return f"{fmt.format(lo)}{suffix}"
        return f"{fmt.format(lo)}–{fmt.format(hi)}{suffix}"

    niveaux_hs_value = _range_value("niveaux_horsol")
    niveaux_ss_value = _range_value("niveaux_ssol")
    hauteur_value = _range_value("hauteur", unit="m", decimals=1)

    col_b1, col_b2, col_b3, col_b4, col_b5, col_b6 = st.columns(6)
    with col_b1:
        st.metric(label="Destination", value=dest_value, help=dest_help)
    with col_b2:
        st.metric(label="Construction", value=constr_value, help=constr_help)
    with col_b3:
        st.metric(
            label="Emprise au sol totale",
            value=emprise_value,
            help=(
                f"Somme de l'emprise au sol de {len(surfaces)} bâtiment(s). "
                "À distinguer de la SRE (surface de référence énergétique)."
            ),
        )
    with col_b4:
        st.metric(
            label="Niveaux hors-sol",
            value=niveaux_hs_value,
            help="Nombre de niveaux hors-sol (min–max des bâtiments sélectionnés).",
        )
    with col_b5:
        st.metric(
            label="Niveaux sous-sol",
            value=niveaux_ss_value,
            help="Nombre de niveaux en sous-sol (min–max des bâtiments sélectionnés).",
        )
    with col_b6:
        st.metric(
            label="Hauteur",
            value=hauteur_value,
            help="Hauteur du bâtiment (min–max des bâtiments sélectionnés).",
        )


# Ordered (column, label) pairs for the building characteristics table.
_BATIMENT_DISPLAY = [
    ("egid", "EGID"),
    ("nombat", "Nom"),
    ("no_batiment", "N° bâtiment"),
    ("commune", "Commune"),
    ("destination", "Destination"),
    ("nomenclature", "Nomenclature"),
    ("nomen_classe", "Classe"),
    ("epoque_construction", "Époque construction"),
    ("annee_construction", "Année construction"),
    ("annee_transformation", "Année transformation"),
    ("niveaux_horsol", "Niveaux hors-sol"),
    ("niveaux_ssol", "Niveaux sous-sol"),
    ("hauteur", "Hauteur"),
    ("surface", "Emprise au sol"),
]


def show_batiments_table(batiment_records: list[dict]) -> None:
    """
    Affiche les caractéristiques des bâtiments (couche SITG CAD_BATIMENT_HORSOL)
    pour les EGID sélectionnés : époque/année de construction, niveaux, hauteur,
    emprise au sol, destination, etc.
    """
    if not batiment_records:
        st.info(
            "Aucune donnée bâtiment (CAD_BATIMENT_HORSOL) trouvée pour ces EGID. "
            "Les données sont mises à jour automatiquement au démarrage puis chaque jour."
        )
        return

    df = pl.from_dicts(batiment_records)
    cols = [c for c, _ in _BATIMENT_DISPLAY if c in df.columns]
    df_display = df.select(cols)

    col_cfg = {
        "egid": st.column_config.TextColumn("EGID"),
        "annee_construction": st.column_config.NumberColumn(
            "Année construction", format="%d"
        ),
        "annee_transformation": st.column_config.NumberColumn(
            "Année transformation", format="%d"
        ),
        "niveaux_horsol": st.column_config.NumberColumn(
            "Niveaux hors-sol", format="%d"
        ),
        "niveaux_ssol": st.column_config.NumberColumn("Niveaux sous-sol", format="%d"),
        "hauteur": st.column_config.NumberColumn("Hauteur", format="%.1f m"),
        "surface": st.column_config.NumberColumn("Emprise au sol", format="%d m²"),
    }
    # Friendly labels for the remaining (text) columns.
    for col, label in _BATIMENT_DISPLAY:
        col_cfg.setdefault(col, st.column_config.TextColumn(label))

    st.caption(f"{len(df_display):,} bâtiment(s) — source SITG CAD_BATIMENT_HORSOL.")
    st.dataframe(
        df_display.to_pandas(),
        column_config=col_cfg,
        width="stretch",
        hide_index=True,
    )

    st.download_button(
        label="📥 Télécharger batiments.xlsx",
        data=convert_df_to_excel(df_display.to_pandas()),
        file_name="batiments.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=False,
    )
