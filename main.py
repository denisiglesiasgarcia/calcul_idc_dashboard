# /main.py

import os
import sqlite3
from datetime import datetime
import polars as pl
import streamlit as st

from sections.helpers.query_IDC import (
    convert_geometry_for_streamlit,
    create_barplot,
    fetch_idc_data,
    refresh_adresses_db,
    show_dataframe,
    show_kpis,
    show_map,
)

st.set_page_config(
    layout="wide",
    page_title="Outil de calcul de l'IDC",
    page_icon="📈",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://www.streamlit.io/community",
        "Report a bug": "https://github.com/yourusername/yourrepo/issues",
        "About": "# My Dashboard\nCreated with Streamlit.",
    },
)

# ---------------------------------------------------------------------------------------
FIELDS = "*"
URL_INDICE_MOYENNES_3_ANS = (
    "https://vector.sitg.ge.ch/arcgis/rest/services/Hosted/"
    "SCANE_INDICE_MOYENNES_3_ANS/FeatureServer/0/query"
)

CURRENT_YEAR = datetime.now().year

# Persist address history across interactions (max 10 entries)
if "address_history" not in st.session_state:
    st.session_state["address_history"] = []


@st.cache_data
def get_all_addresses(db_path: str = "adresses_egid.db") -> pl.DataFrame:
    """
    Load unique address/EGID pairs from SQLite, sorted by address.

    DISTINCT is a safety net against any legacy duplicates that may have
    been inserted before the PRIMARY KEY constraint was enforced.
    """
    abs_path = os.path.abspath(db_path)
    conn = sqlite3.connect(abs_path)
    try:
        return pl.read_database(
            query="SELECT DISTINCT adresse, egid FROM adresses_egid ORDER BY adresse",
            connection=conn,
        )
    except Exception as e:
        print(f"Error in get_all_addresses: {e}")
        return pl.DataFrame(
            {
                "adresse": pl.Series([], dtype=pl.Utf8),
                "egid": pl.Series([], dtype=pl.Utf8),
            }
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------------------
# Sidebar — analysis parameters
# ---------------------------------------------------------------------------------------
with st.sidebar:
    st.header("Paramètres d'analyse")

    seuil = st.number_input(
        label="Seuil IDC de référence [MJ/m²]",
        min_value=0,
        max_value=2000,
        value=450,
        step=10,
        help=(
            "Seuil indicatif pour l'évaluation de la conformité énergétique. "
            "Valeur typique pour bâtiment résidentiel à Genève : 450 MJ/m²."
        ),
    )

    year_range = st.slider(
        label="Période d'analyse",
        min_value=2011,
        max_value=CURRENT_YEAR,
        value=(2011, CURRENT_YEAR),
        step=1,
    )

    st.divider()

    st.subheader("Base de données locale")
    if st.button("Mettre à jour les adresses", use_container_width=True):
        status_text = st.empty()
        progress_bar = st.progress(0.0)
        try:
            n = refresh_adresses_db(
                URL_INDICE_MOYENNES_3_ANS,
                progress_bar=progress_bar,
                status_text=status_text,
            )
            # Clear the single address cache so the multiselect reloads
            get_all_addresses.clear()
            progress_bar.empty()
            status_text.empty()
            st.success(f"{n:,} adresses chargées et enregistrées.")
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"Erreur lors de la mise à jour : {e}")
    st.caption(
        "Les données proviennent de la base SCANE_INDICE_MOYENNES_3_ANS "
        "du SITG (Genève)."
    )

    st.divider()
    st.subheader("Historique des adresses")

    history: list[list[str]] = st.session_state["address_history"]
    if not history:
        st.caption("Aucune adresse consultée pour l'instant.")
    else:
        for i, entry in enumerate(reversed(history)):
            label = ", ".join(a.split(" (")[0] for a in entry)  # strip EGID from label
            if st.button(label, key=f"history_{i}", use_container_width=True):
                # Pre-populate the multiselect by writing to its widget key
                st.session_state["address_multiselect"] = entry
                st.rerun()

# ---------------------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------------------
(tab3,) = st.tabs(["Analyse historique IDC"])

with tab3:
    st.subheader("Sélection adresse")

    # Allow multiselect tags to expand to their full text width instead of
    # truncating with "...". The span inside each tag holds the label text.
    st.markdown(
        """
        <style>
        /* Tag container: remove max-width cap and grow to fit content */
        span[data-baseweb="tag"] {
            max-width: none !important;
            width: fit-content !important;
        }
        /* Inner text span: keep single line, disable overflow clipping */
        span[data-baseweb="tag"] > span:first-child {
            overflow: visible !important;
            white-space: nowrap !important;
            text-overflow: unset !important;
            max-width: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    df_addresses = get_all_addresses()

    # Build display labels and lookup map in a single Polars pass
    df_addresses = df_addresses.with_columns(
        pl.col("egid").cast(pl.Utf8).fill_null("N/A").alias("egid_str")
    ).with_columns(
        (pl.col("adresse") + " (" + pl.col("egid_str") + ")").alias("display")
    )

    display_options = df_addresses["display"].to_list()
    options_map: dict[str, dict] = {
        row["display"]: {"adresse": row["adresse"], "egid": row["egid_str"]}
        for row in df_addresses.to_dicts()
    }

    selected_options = st.multiselect(
        label="Adresse",
        options=display_options,
        default=[],
        placeholder="Sélectionner une ou plusieurs adresses...",
        key="address_multiselect",
    )

    if selected_options:
        st.write(f"{len(selected_options)} adresse(s) sélectionnée(s)")
        selected_rows = [options_map[opt] for opt in selected_options]
        st.session_state["data_verif_idc"] = pl.DataFrame(selected_rows)

        # Update history — avoid duplicates, keep last 10
        history = st.session_state["address_history"]
        if selected_options not in history:
            history.append(selected_options)
            st.session_state["address_history"] = history[-10:]

    # ---------------------------------------------------------------------------------------
    try:
        if selected_options and len(st.session_state.get("data_verif_idc", [])) > 0:
            st.subheader("Plan de situation")

            egids = st.session_state["data_verif_idc"]["egid"].to_list()

            # ------------------------------------------------------------------
            # API cache in session_state — avoids re-fetching when the user only
            # toggles a checkbox or adjusts a sidebar parameter.
            # The cache is invalidated whenever the selected EGID set changes.
            # ------------------------------------------------------------------
            cache_key = tuple(sorted(egids))
            if st.session_state.get("_api_cache_key") != cache_key:
                with st.spinner("Chargement des données SITG..."):
                    data_geometry, data_df = fetch_idc_data(
                        egids, URL_INDICE_MOYENNES_3_ANS
                    )
                st.session_state["_api_cache_key"] = cache_key
                st.session_state["_api_geometry"] = data_geometry
                st.session_state["_api_df"] = data_df
            else:
                data_geometry = st.session_state["_api_geometry"]
                data_df = st.session_state["_api_df"]

            if data_geometry and data_df:
                if st.checkbox("Afficher la carte"):
                    geojson_data, centroid = convert_geometry_for_streamlit(
                        data_geometry
                    )
                    show_map(geojson_data, centroid)

                # KPI row
                st.subheader("Derniers indicateurs clés disponibles")
                show_kpis(data_df, seuil=seuil)

                # Historical bar chart
                st.subheader("Historique IDC")
                adresses_titre = st.session_state["data_verif_idc"]["adresse"].to_list()
                title = ", ".join(adresses_titre)
                create_barplot(data_df, title, seuil=seuil, year_range=year_range)

                if st.checkbox("Afficher les données IDC"):
                    show_dataframe(data_df)
            else:
                st.error(
                    "Pas de données disponibles pour le(s) EGID associé(s) à ce site."
                )
    except Exception as e:
        st.error(f"Une erreur est survenue lors de l'analyse : {e}")
