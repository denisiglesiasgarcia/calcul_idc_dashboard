# /main.py

import os
import pandas as pd
import polars as pl
import streamlit as st
import sqlite3

from sections.helpers.query_IDC import (
    make_request,
    convert_geometry_for_streamlit,
    show_map,
    show_dataframe,
    create_barplot,
)

# streamlit wide mode
st.set_page_config(
    layout="wide",
    page_title="Outil de calcul de l'IDC",
    page_icon="📈",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://www.streamlit.io/community",
        "Report a bug": "https://github.com/yourusername/yourrepo/issues",
        "About": "# My Dashboard\nCreated with Streamlit."
    }
)

# ---------------------------------------------------------------------------------------
# IDC query
FIELDS = "*"
URL_INDICE_MOYENNES_3_ANS = "https://vector.sitg.ge.ch/arcgis/rest/services/Hosted/SCANE_INDICE_MOYENNES_3_ANS/FeatureServer/0/query"

@st.cache_data
def get_all_addresses(db_path: str = "adresses_egid.db") -> pl.DataFrame:
    """Load address/EGID pairs from SQLite. Cached by Streamlit."""
    abs_path = os.path.abspath(db_path)
    conn = sqlite3.connect(abs_path)
    try:
        return pl.read_database(
            query="SELECT adresse, egid FROM adresses_egid ORDER BY adresse",
            connection=conn,
        )
    except Exception as e:
        print(f"Error in get_all_addresses: {e}")
        return pl.DataFrame({"adresse": pl.Series([], dtype=pl.Utf8), "egid": pl.Series([], dtype=pl.Utf8)})
    finally:
        conn.close()

# ---------------------------------------------------------------------------------------
# Define the default tabs
tabs = [
    "Analyse historique IDC",
]
(tab3,) = st.tabs(tabs)  # unpack the single-element tuple

# ---------------------------------------------------------------------------------------
with tab3:
    st.subheader("Sélection adresse")

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
    )

    if selected_options:
        st.write(f"{len(selected_options)} adresse(s) sélectionnée:")

        selected_rows = [options_map[opt] for opt in selected_options]
        # Store as Polars DataFrame
        st.session_state["data_verif_idc"] = pl.DataFrame(selected_rows)
    else:
        st.warning("Sélectionner au moins une adresse pour continuer.")


    # ---------------------------------------------------------------------------------------
    st.subheader("Plan de situation")

    if selected_options and len(st.session_state.get("data_verif_idc", [])) > 0:
        egids = st.session_state["data_verif_idc"]["egid"].to_list()

        data_geometry = make_request(
            0, FIELDS, URL_INDICE_MOYENNES_3_ANS, 1000,
            "SCANE_INDICE_MOYENNES_3_ANS", True, egids,
        )
        data_df = make_request(
            0, FIELDS, URL_INDICE_MOYENNES_3_ANS, 1000,
            "SCANE_INDICE_MOYENNES_3_ANS", False, egids,
        )

        if data_geometry and data_df:
            if st.checkbox("Afficher la carte"):
                geojson_data, centroid = convert_geometry_for_streamlit(data_geometry)
                show_map(geojson_data, centroid)

            st.subheader("Historique IDC")
            adresses_titre = st.session_state["data_verif_idc"]["adresse"].to_list()
            title = ", ".join(adresses_titre)
            create_barplot(data_df, title)

            if st.checkbox("Afficher les données IDC"):
                show_dataframe(data_df)
        else:
            st.error("Pas de données disponibles pour le(s) EGID associé(s) à ce site.")
    else:
        st.write("Pas d'adresse sélectionnée.")