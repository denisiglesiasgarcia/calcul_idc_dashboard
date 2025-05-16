# /main.py

import os
import datetime
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

from sections.helpers.calcul_dj import (
    get_meteo_data,
)

from sections.helpers.affectations_idc_sre import (
    display_affectations_idc,
    AFFECTATION_OPTIONS
)

from sections.helpers.agents_energetiques_idc import (
    display_agents_energetiques_idc,
    OPTIONS_AGENT_ENERGETIQUE_IDC,
    OPTIONS_AGENT_ENERGETIQUE_IDC_ECS
)

from sections.helpers.note_calcul.remarques_idc import (
    remarques_note_calcul_idc
)

from sections.helpers.note_calcul_idc_main import (
    fonction_note_calcul_idc_dataframe,
    fonction_note_calcul_idc,
)

from sections.helpers.resultats_idc import (
    show_results_idc
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

# Mise à jour météo
last_update_time_meteo = datetime.datetime(2021, 1, 1)
now = datetime.datetime.now()
if (now - last_update_time_meteo).days > 1:
    last_update_time_meteo = now
    st.session_state["df_meteo_tre200d0"] = get_meteo_data()

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
    "Calculer un IDC",
    "Note de calcul IDC",
    "Vérifier un IDC",
]
tab1, tab2, tab3 = st.tabs(tabs)

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
with tab1:
    st.subheader("Eléments à renseigner pour le calcul de l'IDC", divider="rainbow")
    
    # Create action buttons at the top
    action_col1, action_col2 = st.columns([1, 4])
    with action_col1:
        reset_button = st.button("🔄 Réinitialiser", key="reset_idc_inputs", type="secondary")

    # Reset all values if reset button is clicked
    if reset_button:
        # Create a list of all keys to reset
        reset_keys = [
            "idc_sre_m2",
            "comptage_ecs_inclus",
            "idc_somme_agents_energetiques_mj",
            "somme_pourcentage_affectations",
            "idc_ecs_somme_agents_energetiques_mj", 
            "adresse_multiselect",
            "calcul_idc_data_df",
        ]
        
        # Add all agent-specific keys
        for option in OPTIONS_AGENT_ENERGETIQUE_IDC:
            reset_keys.append(option["variable"])
        for option in OPTIONS_AGENT_ENERGETIQUE_IDC_ECS:
            reset_keys.append(option["variable"])
        
        # Add all affectation keys
        for option in AFFECTATION_OPTIONS:
            reset_keys.append(option["variable"])
        
        # Reset all values in session state
        for key in reset_keys:
            if key in st.session_state["data_site"]:
                if key == "adresse_multiselect":
                    # For DataFrame, set to empty DataFrame
                    st.session_state["data_site"][key] = pd.DataFrame(columns=["adresse", "egid"])
                elif key == "calcul_idc_data_df":
                    # For historical data, set to empty list
                    st.session_state["data_site"][key] = []
                else:
                    # For numeric values, set to 0.0
                    st.session_state["data_site"][key] = 0.0
        
        # Set default affectation (habitat collectif to 100%)
        st.session_state["data_site"]["sre_pourcentage_habitat_collectif"] = 100.0
        
        # Reset comptage ECS option
        st.session_state["data_site"]["comptage_ecs_inclus"] = True
        
        # Reset radio button state
        if "comptage_ecs_radio_state" in st.session_state:
            st.session_state["comptage_ecs_radio_state"] = "comptage_inclus"
        
        # Reset callback calculation state
        st.session_state["data_site"]["calculate_requested"] = False

        # Reset multiselect widgets
        if "calcul_idc_adresse_multiselect" in st.session_state:
            st.session_state["calcul_idc_adresse_multiselect"] = []
        
        # Reset calculation complete
        if "calculation_complete" in st.session_state:
            st.session_state["calculation_complete"] = False

        st.success("Valeurs réinitialisées avec succès!")
        st.rerun()  # Rerun the app to reflect changes

    # Store inputs in a container
    input_container = st.container(border=False)
    input_container_adresse = st.container(border=True)
    input_container_date = st.container(border=True)
    input_container_sre_ecs = st.container(border=True)
    input_container_agents = st.container(border=True)
    input_container_agents_ecs = st.container(border=True)
    
    with input_container:
        # Adresse
        with input_container_adresse:
            st.markdown(
                '<span style="font-size:1.2em;">**Sélectionner une adresse**</span>',
                unsafe_allow_html=True,
            )
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
                placeholder="Select one or more addresses...",
                key="calcul_idc_adresse_multiselect"
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
                st.session_state["data_site"]["adresse_multiselect"] = pd.DataFrame(selected_data)
                
                # Display the selected data
                st.dataframe(st.session_state["data_site"]["adresse_multiselect"], hide_index=True)

            else:
                st.warning("Sélectionner une adresse pour continuer.")
            
            if selected_options and len(st.session_state["data_site"]["adresse_multiselect"]) > 0:
                # get egids
                egids = st.session_state["data_site"]["adresse_multiselect"]["egid"].tolist()

                # get data
                calcul_idc_data_geometry = make_request(
                    0,
                    FIELDS,
                    URL_INDICE_MOYENNES_3_ANS,
                    1000,
                    "SCANE_INDICE_MOYENNES_3_ANS",
                    True,
                    egids,
                )
                st.session_state["data_site"]["calcul_idc_data_df"] = make_request(
                    0,
                    FIELDS,
                    URL_INDICE_MOYENNES_3_ANS,
                    1000,
                    "SCANE_INDICE_MOYENNES_3_ANS",
                    False,
                    egids,
                )
                if calcul_idc_data_geometry and st.session_state["data_site"]["calcul_idc_data_df"] :
                    # show map
                    if st.checkbox("Afficher la carte"):
                        calcul_idc_geojson_data, calcul_idc_centroid = convert_geometry_for_streamlit(
                            calcul_idc_data_geometry
                        )
                        show_map(calcul_idc_geojson_data, calcul_idc_centroid)

                    if st.checkbox("Afficher graphique historique"):
                        # create barplot
                        adresses_titre = st.session_state["data_site"]["adresse_multiselect"]["adresse"].tolist()
                        title = ', '.join(adresses_titre)
                        create_barplot(st.session_state["data_site"]["calcul_idc_data_df"], title)

                    # show dataframe in something hidden like a
                    if st.checkbox("Afficher les données IDC"):
                        show_dataframe(st.session_state["data_site"]["calcul_idc_data_df"])
                else:
                    st.error(
                        "Pas de données disponibles pour le(s) EGID associé(s) à ce site."
                    )
            else:
                st.write("Pas d'adresse sélectionnée.")
            
            # informations en provenance du calcul_idc_data_df
            if ("calcul_idc_data_df" in st.session_state["data_site"] and
                len(st.session_state["data_site"]["calcul_idc_data_df"])) > 0:
                # Check if calcul_idc_data_df is a list or DataFrame
                if isinstance(st.session_state["data_site"]["calcul_idc_data_df"], list):
                    # Convert to DataFrame if it's a list
                    df_historical = pd.DataFrame(st.session_state["data_site"]["calcul_idc_data_df"])
                else:
                    df_historical = st.session_state["data_site"]["calcul_idc_data_df"]
                
                # Estimation dates début/fin de période
                if "date_debut_periode" in df_historical.columns:
                    periode_start_estimation = pd.to_datetime(
                        df_historical["date_debut_periode"]
                    ).max() + pd.DateOffset(years=1)
                if "date_fin_periode" in df_historical.columns:
                    periode_end_estimation = pd.to_datetime(
                        df_historical["date_fin_periode"]
                    ).max() + pd.DateOffset(years=1)
                
                # IDC
                sre_estimation = float(df_historical[df_historical["date_debut_periode"] == (df_historical["date_debut_periode"]).max()]["sre"].iloc[0])
                
        # dates
        with input_container_date:
            st.markdown(
                '<span style="font-size:1.2em;">**Sélectionner les dates de début et fin de période**</span>',
                unsafe_allow_html=True,
            )
            tab2_col3, tab2_col4 = st.columns(2)
            # dates
            with tab2_col3:
                if ("calcul_idc_data_df" in st.session_state["data_site"] and
                    len(st.session_state["data_site"]["calcul_idc_data_df"])) > 0:
                    periode_start_estimation_input = pd.to_datetime(periode_start_estimation)
                else:
                    periode_start_estimation_input = pd.to_datetime(
                    st.session_state["df_meteo_tre200d0"]["time"].max()
                ) - pd.DateOffset(days=365)
                periode_start = st.date_input(
                    "Début de la période",
                    datetime.date(
                        periode_start_estimation_input.year,
                        periode_start_estimation_input.month,
                        periode_start_estimation_input.day
                    ),
                )

            with tab2_col4:
                max_date_texte = (
                    st.session_state["df_meteo_tre200d0"]["time"]
                    .max()
                    .strftime("%Y-%m-%d")
                )
                fin_periode_txt = (
                    f"Fin de la période (météo disponible jusqu'au: {max_date_texte})"
                )
                max_date = pd.to_datetime(
                    st.session_state["df_meteo_tre200d0"]["time"].max()
                )
                if ("calcul_idc_data_df" in st.session_state["data_site"] and
                    len(st.session_state["data_site"]["calcul_idc_data_df"])) > 0:
                    periode_end_estimation_input = min(max_date,periode_end_estimation)
                else:
                    periode_end_estimation_input = max_date
                periode_end = st.date_input(
                    fin_periode_txt,
                    datetime.date(
                        periode_end_estimation_input.year,
                        periode_end_estimation_input.month,
                        periode_end_estimation_input.day
                        ),
                )

            # Process date info
            periode_nb_jours = (periode_end - periode_start).days + 1
            st.session_state["data_site"]["periode_nb_jours"] = float(periode_nb_jours)
            st.session_state["data_site"]["periode_start"] = pd.to_datetime(periode_start)
            st.session_state["data_site"]["periode_end"] = pd.to_datetime(periode_end)

            # Display period validation message
            date_valid = True
            try:
                if st.session_state["data_site"]["periode_nb_jours"] <= 180:
                    st.warning(
                        "La période de mesure doit être supérieure à 3 mois (minimum recommandé 6 mois)"
                    )
                    date_valid = False
            except ValueError:
                st.warning("Problème de date de début et de fin de période")
                date_valid = False
            
            st.success(
                f"Période du **{st.session_state['data_site']['periode_start'].strftime('%Y-%m-%d')}** au **{st.session_state['data_site']['periode_end'].strftime('%Y-%m-%d')}** soit **{int(st.session_state['data_site']['periode_nb_jours'])} jours**"
            )
        
        with input_container_sre_ecs:
            tab2_col1, tab2_col2 = st.columns(2)
            with tab2_col1:
                # SRE
                st.markdown(
                    '<span style="font-size:1.2em;">**Surface de référence énergétique**</span>',
                    unsafe_allow_html=True,
                )
                
                # Determine the default value
                # First check if we have a value from historical data
                if 'sre_estimation' in locals() and sre_estimation > 0:
                    default_sre = sre_estimation
                else:
                    # Otherwise use the current idc_sre_m2 value if available, otherwise fall back to sre_renovation_m2
                    current_sre = st.session_state["data_site"].get("idc_sre_m2", 0.0)
                    if current_sre == 0.0:
                        current_sre = st.session_state["data_site"].get("sre_renovation_m2", 0.0)
                    default_sre = current_sre
                
                idc_sre_m2 = st.number_input(
                    "Surface de référence énergétique (m2)",
                    min_value=0.0,
                    value=default_sre,
                    key="idc_sre_m2_input"
                )
                st.session_state["data_site"]["idc_sre_m2"] = idc_sre_m2
                
                # Validate SRE input
                sre_valid = idc_sre_m2 > 0
                if not sre_valid:
                    st.warning("La surface de référence énergétique doit être supérieure à 0")

            with tab2_col2:
                # Production ECS
                st.markdown(
                    '<span style="font-size:1.2em;">**Production ECS**</span>',
                    unsafe_allow_html=True,
                )
                
                # Ensure the variable exists (default to True if not present)
                if "comptage_ecs_inclus" not in st.session_state["data_site"]:
                    st.session_state["data_site"]["comptage_ecs_inclus"] = True
                
                # Create a key for storing the radio button state separate from the data value
                if "comptage_ecs_radio_state" not in st.session_state:
                    st.session_state["comptage_ecs_radio_state"] = "comptage_inclus" if st.session_state["data_site"]["comptage_ecs_inclus"] else "comptage_separe"
                
                # Define a callback function to update both states at once
                def update_comptage_ecs():
                    selected_option = st.session_state["comptage_ecs_option_input"]
                    st.session_state["comptage_ecs_radio_state"] = selected_option
                    st.session_state["data_site"]["comptage_ecs_inclus"] = (selected_option == "comptage_inclus")
                
                # Use radio buttons with the separate state
                comptage_ecs_option = st.radio(
                    "Type de comptage ECS:",
                    options=["comptage_inclus", "comptage_separe"],
                    format_func=lambda x: "Comprise dans les relevés" if x == "comptage_inclus" else "Non-comprise dans les relevés",
                    key="comptage_ecs_option_input",
                    index=0 if st.session_state["comptage_ecs_radio_state"] == "comptage_inclus" else 1,
                    on_change=update_comptage_ecs
                )

        # Create expandable sections for the remaining inputs
        with input_container_agents:
            tab3_col1, tab3_col2 = st.columns(2)
            with tab3_col1:
                # Agents énergétiques
                st.session_state["data_site"]["idc_somme_agents_energetiques_mj"] = (
                    display_agents_energetiques_idc(
                        st.session_state["data_site"],
                        is_ecs=False
                    )
                )
                
                # Store energy agents validation status
                energy_agents_valid = st.session_state["data_site"]["idc_somme_agents_energetiques_mj"] > 0

            with tab3_col2:
                # Affectations SRE
                preselected_affectations = []
                for option in AFFECTATION_OPTIONS:
                    if st.session_state["data_site"].get(option["variable"], 0) > 0:
                        preselected_affectations.append(option["label"])
                
                # Now call the function with the pre-selected options
                st.session_state["data_site"]["somme_pourcentage_affectations"] = (
                    display_affectations_idc(
                        st.session_state["data_site"]["idc_sre_m2"], 
                        st.session_state["data_site"]  # Pass the data_site as data_sites_db parameter
                    )
                )
                
                # Store affectations validation status
                affectations_valid = st.session_state["data_site"]["somme_pourcentage_affectations"] == 100.0
        
        # Only show ECS section if separate comptage is selected
        ecs_agents_valid = True  # Default to valid if comptage is included
        if not st.session_state["data_site"]["comptage_ecs_inclus"]:
            with input_container_agents_ecs:
                st.session_state["data_site"]["idc_ecs_somme_agents_energetiques_mj"] = (
                    display_agents_energetiques_idc(
                        st.session_state["data_site"],
                        is_ecs=True
                    )
                )
                
                # Store ECS energy agents validation status
                ecs_agents_valid = st.session_state["data_site"]["idc_ecs_somme_agents_energetiques_mj"] > 0
                if not ecs_agents_valid:
                    st.warning("Veuillez renseigner au moins un agent énergétique ECS")
      
   
    # Check if all inputs are valid
    all_valid = (
                    date_valid and
                    sre_valid and
                    energy_agents_valid and
                    affectations_valid and
                    ecs_agents_valid
                    )
        
    # Create validation summary if needed
    if not all_valid:
        validation_message = "Veuillez corriger les erreurs suivantes avant de calculer l'IDC:"
        validation_issues = []
        
        if not date_valid:
            validation_issues.append("- La période doit être supérieure à 3 mois")
        if not sre_valid:
            validation_issues.append("- La surface de référence énergétique doit être supérieure à 0")
        if not energy_agents_valid:
            validation_issues.append("- Veuillez renseigner au moins un agent énergétique")
        if not affectations_valid:
            validation_issues.append("- La somme des pourcentages d'affectation doit être égale à 100%")
        if not st.session_state["data_site"]["comptage_ecs_inclus"] and not ecs_agents_valid:
            validation_issues.append("- Veuillez renseigner au moins un agent énergétique ECS")
            
        st.warning(validation_message + "\n\n" + "\n".join(validation_issues))
           
    # Show results if calculation is complete
    if all_valid and st.button("Calculer l'IDC", type="primary"):
        st.session_state["data_site"] = fonction_note_calcul_idc(
                    st.session_state["data_site"],
                    st.session_state["df_meteo_tre200d0"],
                )

        st.subheader("Résultats du calcul de l'IDC", divider="rainbow")
        
        # Check if the required data is available
        if (st.session_state["data_site"]["idc_sre_m2"] > 0 and
            st.session_state["data_site"]["somme_pourcentage_affectations"] > 0 and
            st.session_state["data_site"]["idc_somme_agents_energetiques_mj"] > 0 and
            st.session_state["data_site"]["dj_periode"] > 1):
            show_results_idc(st.session_state["data_site"])
        else:
            st.error(
                "Erreur dans le calcul de l'IDC. Veuillez vérifier les données saisies."
            )
        st.download_button(
            label="📥 Télécharger les résultats",
            data=f"IDC: {st.session_state['data_site'].get('idc_resultat_comptage_ecs_inclus_mj_m2', 0):.2f} MJ/m²\n" +
                f"Période: {st.session_state['data_site']['periode_start'].strftime('%Y-%m-%d')} au {st.session_state['data_site']['periode_end'].strftime('%Y-%m-%d')}\n" +
                f"SRE: {st.session_state['data_site']['idc_sre_m2']:.2f} m²",
            file_name=f"IDC_resultat_{datetime.datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
        )

    # Optionally display debug information
    with st.expander("Debug", expanded=False):
        st.write("État du radio button:", st.session_state.get("comptage_ecs_radio_state", "Non défini"))
        st.write(st.session_state["data_site"])

with tab2:
    # ---------------------------------------------------------------------------------------
    st.subheader("Notes de calcul", divider="rainbow")
    try:
        # Check if the required data is available
        if (st.session_state["data_site"]["idc_sre_m2"] > 0 and
        st.session_state["data_site"]["somme_pourcentage_affectations"] > 0 and
        st.session_state["data_site"]["idc_somme_agents_energetiques_mj"] > 0 and
        st.session_state["data_site"]["dj_periode"] > 1):
            (
                df_periode_list,
                df_list_idc,
                df_agent_energetique_idc_sum,
                df_agent_energetique_idc_mazout,
                df_agent_energetique_idc_gaz_naturel,
                df_agent_energetique_idc_bois_buches_dur,
                df_agent_energetique_idc_bois_buches_tendre,
                df_agent_energetique_idc_pellets,
                df_agent_energetique_idc_plaquettes,
                df_agent_energetique_idc_cad_reparti,
                df_agent_energetique_idc_cad_tarife,
                df_agent_energetique_idc_electricite_pac_avant,
                df_agent_energetique_idc_electricite_pac_apres,
                df_agent_energetique_idc_electricite_directe,
                df_agent_energetique_idc_autre,
            ) = fonction_note_calcul_idc_dataframe(
                st.session_state["data_site"],
                st.session_state["df_meteo_tre200d0"],
            )
            
            st.markdown("##### Période de calcul")
            st.dataframe(
                df_periode_list,
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("##### Calcul IDC")
            st.dataframe(
                df_list_idc,
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("##### Agents énergétiques")
            st.dataframe(
                df_agent_energetique_idc_sum,
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("###### Mazout")
            st.dataframe(
                df_agent_energetique_idc_mazout,
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("###### Gaz naturel")
            st.dataframe(
                df_agent_energetique_idc_gaz_naturel,
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("###### Bois bûches dur")
            st.dataframe(
                df_agent_energetique_idc_bois_buches_dur,
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("###### Bois bûches tendre")
            st.dataframe(
                df_agent_energetique_idc_bois_buches_tendre,
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("###### Pellets")
            st.dataframe(
                df_agent_energetique_idc_pellets,
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("###### Plaquettes")
            st.dataframe(
                df_agent_energetique_idc_plaquettes,
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("###### CAD réparti")
            st.dataframe(
                df_agent_energetique_idc_cad_reparti,
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("###### CAD tarifé")
            st.dataframe(
                df_agent_energetique_idc_cad_tarife,
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("###### Electricité PAC avant")
            st.dataframe(
                df_agent_energetique_idc_electricite_pac_avant,
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("###### Electricité PAC après")
            st.dataframe(
                df_agent_energetique_idc_electricite_pac_apres,
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("###### Electricité directe")
            st.dataframe(
                df_agent_energetique_idc_electricite_directe,
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("###### Autre")
            st.dataframe(
                df_agent_energetique_idc_autre,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning("Veuillez d'abord renseigner l'onglet 'Calculer un IDC' avant de générer la note de calcul.")
    except Exception as e:
        st.error(f"Erreur inattendue: {e}")
    # remaques note calcul idc
    remarques_note_calcul_idc()

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