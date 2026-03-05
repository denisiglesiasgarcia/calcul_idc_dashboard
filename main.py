# /main.py

import os
import pandas as pd
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
def get_all_addresses(db_path: str = "adresses_egid.db") -> pd.DataFrame:
    """
    Get all addresses from the database for the dropdown list.
    Results are cached by Streamlit.
    """
    # Use absolute path for better reliability
    abs_path = os.path.abspath(db_path)
    
    # Debug info
    # print(f"Connecting to database at: {abs_path}")
    
    conn = sqlite3.connect(abs_path)
    try:
        query = "SELECT adresse, egid FROM adresses_egid ORDER BY adresse"
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"Error in get_all_addresses: {e}")
        # Return empty DataFrame if there's an error
        return pd.DataFrame(columns=["adresse", "egid"])
    finally:
        conn.close()

# ---------------------------------------------------------------------------------------
# Define the default tabs
tabs = [
    "Analyse historique IDC",
]
(tab3,) = st.tabs(tabs)  # unpack the single-element tuple

# Initialize all form values at the beginning of your script
def initialize_data_site():
    if "data_site" not in st.session_state:
        st.session_state["data_site"] = {}
        
    # Initialize all potential values with defaults if they don't exist
    defaults = {
        "periode_nb_jours":0,
        "idc_sre_m2":0,
        "comptage_ecs_inclus":True,
        "idc_agent_energetique_ef_cad_reparti_kwh":0,
        "idc_agent_energetique_ef_cad_tarife_kwh":0,
        "idc_agent_energetique_ef_electricite_pac_avant_kwh":0,
        "idc_agent_energetique_ef_electricite_pac_apres_kwh":0,
        "idc_agent_energetique_ef_electricite_directe_kwh":0,
        "idc_agent_energetique_ef_gaz_naturel_m3":0,
        "idc_agent_energetique_ef_gaz_naturel_kwh":0,
        "idc_agent_energetique_ef_mazout_litres":0,
        "idc_agent_energetique_ef_mazout_kg":0,
        "idc_agent_energetique_ef_mazout_kwh":0,
        "idc_agent_energetique_ef_bois_buches_dur_stere":0,
        "idc_agent_energetique_ef_bois_buches_tendre_stere":0,
        "idc_agent_energetique_ef_bois_buches_tendre_kwh":0,
        "idc_agent_energetique_ef_pellets_m3":0,
        "idc_agent_energetique_ef_pellets_kg":0,
        "idc_agent_energetique_ef_pellets_kwh":0,
        "idc_agent_energetique_ef_plaquettes_m3":0,
        "idc_agent_energetique_ef_plaquettes_kwh":0,
        "idc_agent_energetique_ef_autre_kwh":0,
        "idc_somme_agents_energetiques_mj":0,
        "sre_pourcentage_habitat_collectif":100,
        "sre_pourcentage_habitat_individuel":0,
        "sre_pourcentage_administration":0,
        "sre_pourcentage_ecoles":0,
        "sre_pourcentage_commerce":0,
        "sre_pourcentage_restauration":0,
        "sre_pourcentage_lieux_de_rassemblement":0,
        "sre_pourcentage_hopitaux":0,
        "sre_pourcentage_industrie":0,
        "sre_pourcentage_depots":0,
        "sre_pourcentage_installations_sportives":0,
        "sre_pourcentage_piscines_couvertes":0,
        "somme_pourcentage_affectations":0,
        "idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2":0,
        "idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj":0,
        "idc_bh_energie_finale_chauffage_comptage_ecs_inclus_mj":0,
        "idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_inclus_mj_m2":0,
        "idc_resultat_comptage_ecs_inclus_mj_m2":0,
        "idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj":0,
        "idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2":0,
        "idc_bh_energie_finale_chauffage_comptage_ecs_non_inclus_mj":0,
        "idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_non_inclus_mj_m2":0,
        "idc_resultat_comptage_ecs_non_inclus_mj_m2":0,
        "idc_ecs_agent_energetique_ef_cad_reparti_kwh":0,
        "idc_ecs_agent_energetique_ef_cad_tarife_kwh":0,
        "idc_ecs_agent_energetique_ef_electricite_pac_avant_kwh":0,
        "idc_ecs_agent_energetique_ef_electricite_pac_apres_kwh":0,
        "idc_ecs_agent_energetique_ef_electricite_directe_kwh":0,
        "idc_ecs_agent_energetique_ef_gaz_naturel_m3":0,
        "idc_ecs_agent_energetique_ef_gaz_naturel_kwh":0,
        "idc_ecs_agent_energetique_ef_mazout_litres":0,
        "idc_ecs_agent_energetique_ef_mazout_kg":0,
        "idc_ecs_agent_energetique_ef_mazout_kwh":0,
        "idc_ecs_agent_energetique_ef_bois_buches_dur_stere":0,
        "idc_ecs_agent_energetique_ef_bois_buches_tendre_stere":0,
        "idc_ecs_agent_energetique_ef_bois_buches_tendre_kwh":0,
        "idc_ecs_agent_energetique_ef_pellets_m3":0,
        "idc_ecs_agent_energetique_ef_pellets_kg":0,
        "idc_ecs_agent_energetique_ef_pellets_kwh":0,
        "idc_ecs_agent_energetique_ef_plaquettes_m3":0,
        "idc_ecs_agent_energetique_ef_plaquettes_kwh":0,
        "idc_ecs_agent_energetique_ef_autre_kwh":0,
        "idc_agent_energetique_ef_mazout_somme_mj":0,
        "idc_agent_energetique_ef_gaz_naturel_somme_mj":0,
        "idc_agent_energetique_ef_bois_buches_dur_somme_mj":0,
        "idc_agent_energetique_ef_bois_buches_tendre_somme_mj":0,
        "idc_agent_energetique_ef_pellets_somme_mj":0,
        "idc_agent_energetique_ef_plaquettes_somme_mj":0,
        "idc_agent_energetique_ef_cad_reparti_somme_mj":0,
        "idc_agent_energetique_ef_cad_tarife_somme_mj":0,
        "idc_agent_energetique_ef_electricite_pac_avant_somme_mj":0,
        "idc_agent_energetique_ef_electricite_pac_apres_somme_mj":0,
        "idc_agent_energetique_ef_electricite_directe_somme_mj":0,
        "idc_agent_energetique_ef_autre_somme_mj":0,
        "calculate_requested": False,
        "dj_periode":0,
        "calculation_complete": False,

    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state["data_site"]:
            st.session_state["data_site"][key] = default_value

# Call this function at the start of your app
initialize_data_site()

# ---------------------------------------------------------------------------------------
with tab3:
    st.subheader("Sélection adresse")

    # Modify your get_all_addresses function to use absolute path
    

    # Get all addresses from the database
    df = get_all_addresses()

    # Create combined options for the multiselect with address and EGID
    # First make sure there are no missing values
    df_display = df.copy()
    df_display.fillna({"egid": "N/A"}, inplace=True)

    # Create a combined display string for each address
    display_options = [f"{row['adresse']} ({row['egid']})" for _, row in df_display.iterrows()]

    # Create a dictionary to map display options back to the original data
    options_map = {f"{row['adresse']} ({row['egid']})": {"adresse": row['adresse'], "egid": row['egid']} 
                for _, row in df_display.iterrows()}

    # Display the multiselect with combined address and EGID
    selected_options = st.multiselect(
        label="Adresse",
        options=display_options,
        default=[],
        placeholder="Select one or more addresses..."
    )

    # Check if any addresses are selected
    if selected_options:
        st.write(f"{len(selected_options)} adresse(s) sélectionnée:")
        
        # Create a list to store selected addresses and EGIDs
        selected_addresses = []
        selected_egids = []
        
        # Extract the selected addresses and EGIDs from the options map
        for option in selected_options:
            selected_addresses.append(options_map[option]["adresse"])
            selected_egids.append(options_map[option]["egid"])
        
        # Create a dataframe of selected items
        selected_data = {
            "adresse": selected_addresses,
            "egid": selected_egids
        }
        st.session_state["data_verif_idc"] = pd.DataFrame(selected_data)
        
        # Display the selected data
        # st.dataframe(selected_df)

    else:
        st.warning("Sélectionner au moins une adresse pour continuer.")


    # ---------------------------------------------------------------------------------------
    st.subheader("Plan de situation")

    if selected_options and len(st.session_state["data_verif_idc"]) > 0:
        # get egids
        egids = st.session_state["data_verif_idc"]["egid"].tolist()

        # get data
        data_geometry = make_request(
            0,
            FIELDS,
            URL_INDICE_MOYENNES_3_ANS,
            1000,
            "SCANE_INDICE_MOYENNES_3_ANS",
            True,
            egids,
        )
        data_df = make_request(
            0,
            FIELDS,
            URL_INDICE_MOYENNES_3_ANS,
            1000,
            "SCANE_INDICE_MOYENNES_3_ANS",
            False,
            egids,
        )

        if data_geometry and data_df:
            # show map
            if st.checkbox("Afficher la carte"):
                geojson_data, centroid = convert_geometry_for_streamlit(
                    data_geometry
                )
                show_map(geojson_data, centroid)

            st.subheader("Historique IDC")
            # create barplot
            adresses_titre = st.session_state["data_verif_idc"]["adresse"].tolist()
            title = ', '.join(adresses_titre)
            create_barplot(data_df, title)

            # show dataframe in something hidden like a
            if st.checkbox("Afficher les données IDC"):
                show_dataframe(data_df)
        else:
            st.error(
                "Pas de données disponibles pour le(s) EGID associé(s) à ce site."
            )
    else:
        st.write("Pas d'adresse sélectionnée.")