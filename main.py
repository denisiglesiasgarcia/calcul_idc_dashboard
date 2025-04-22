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
    display_affectations_idc
)

from sections.helpers.agents_energetiques_idc import (
    display_agents_energetiques_idc
)

from sections.helpers.note_calcul.remarques_idc import (
    remarques_note_calcul_idc
)

from sections.helpers.note_calcul_idc_main import (
    fonction_note_calcul_idc,
)

from sections.helpers.resultats_idc import (
    display_resultats_idc
)

# streamlit wide mode
st.set_page_config(layout="wide")

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
    "Vérifier IDC",
    "Calculer un IDC",
    "Note de calcul IDC",
]
tab1, tab2, tab3 = st.tabs(tabs)

# initialize st.session_state["data_site"]
if "data_site" not in st.session_state:
    st.session_state["data_site"] = {}

# ---------------------------------------------------------------------------------------
with tab1:
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

with tab2:
    # ---------------------------------------------------------------------------------------
    st.subheader("Eléments à renseigner pour le calcul de l'IDC", divider="rainbow")

    st.markdown(
        '<span style="font-size:1.2em;">**Sélectionner les dates de début et fin de période**</span>',
        unsafe_allow_html=True,
    )
    tab2_col3, tab2_col4 = st.columns(2)
    # dates
    with tab2_col3:
        last_year = pd.to_datetime(
            st.session_state["df_meteo_tre200d0"]["time"].max()
        ) - pd.DateOffset(days=365)
        periode_start = st.date_input(
            "Début de la période",
            datetime.date(last_year.year, last_year.month, last_year.day),
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
        periode_end = st.date_input(
            fin_periode_txt,
            datetime.date(max_date.year, max_date.month, max_date.day),
        )

    periode_nb_jours = (periode_end - periode_start).days + 1
    st.session_state["data_site"]["periode_nb_jours"] = float(periode_nb_jours)

    st.session_state["data_site"]["periode_start"] = pd.to_datetime(
        periode_start
    )
    st.session_state["data_site"]["periode_end"] = pd.to_datetime(periode_end)

    try:
        if st.session_state["data_site"]["periode_nb_jours"] <= 180:
            st.warning(
                "La période de mesure doit être supérieure à 3 mois (minimum recommandé 6 mois)"
            )
    except ValueError:
        st.warning("Problème de date de début et de fin de période")
    st.write(
        f"Période du {st.session_state['data_site']['periode_start'].strftime('%Y-%m-%d')} au {st.session_state['data_site']['periode_end'].strftime('%Y-%m-%d')} soit {int(st.session_state['data_site']['periode_nb_jours'])} jours"
    )

    tab2_col1, tab2_col2 = st.columns(2)
    with tab2_col1:
        # SRE
        st.markdown(
            '<span style="font-size:1.2em;">**Surface de référence énergétique**</span>',
            unsafe_allow_html=True,
        )
        st.session_state["data_site"]["idc_sre_m2"] = st.number_input(
            "Surface de référence énergétique (m2)",
            value=st.session_state["data_site"].get("sre_renovation_m2", 0.0),
        )

    with tab2_col2:
        # Production ECS
        st.markdown(
            '<span style="font-size:1.2em;">**Production ECS**</span>',
            unsafe_allow_html=True,
        )
        
        # Get the default value from session state
        default_option = "comptage_inclus" if st.session_state["data_site"].get("comptage_ecs_inclus", True) else "comptage_separe"
        
        # Use radio buttons for mutually exclusive options
        comptage_ecs_option = st.radio(
            "Type de comptage ECS:",
            options=["comptage_inclus", "comptage_separe"],
            format_func=lambda x: "Comprise dans les relevés" if x == "comptage_inclus" else "Non-comprise dans les relevés",
            index=0 if default_option == "comptage_inclus" else 1
        )
        
        # Update the session state based on selection
        st.session_state["data_site"]["comptage_ecs_inclus"] = (comptage_ecs_option == "comptage_inclus")

        # Only show ECS section if separate comptage is selected
        if comptage_ecs_option == "comptage_separe":
            st.session_state["data_site"]["idc_somme_agents_energetiques_mj"] = (
                display_agents_energetiques_idc(
                    st.session_state["data_site"],
                    is_ecs=True
                )
            )

    tab3_col1, tab3_col2 = st.columns(2)
    with tab3_col1:
        # Agents énergétiques
        st.session_state["data_site"]["idc_somme_agents_energetiques_mj"] = (
            display_agents_energetiques_idc(
                st.session_state["data_site"],
                is_ecs=False
            )
        )

    with tab3_col2:
        # Affectations SRE
        st.session_state["data_site"]["somme_pourcentage_affectations"] = (
            display_affectations_idc(st.session_state["data_site"]["idc_sre_m2"])
        )
        

    # Subheader for the calculation period section
    st.subheader("Résultats du calcul de l'IDC", divider="rainbow")
    display_resultats_idc(
        st.session_state["data_site"],)
    
    
    st.subheader("Debug", divider="rainbow")
    st.write(st.session_state["data_site"])

with tab3:
    # ---------------------------------------------------------------------------------------
    st.subheader("Notes de calcul", divider="rainbow")
    if (st.session_state["data_site"]["idc_sre_m2"] > 0 and
    st.session_state["data_site"]["somme_pourcentage_affectations"] > 0 and
    st.session_state["data_site"]["idc_somme_agents_energetiques_mj"] > 0):
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
        ) = fonction_note_calcul_idc(
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
    # remaques note calcul idc
    remarques_note_calcul_idc()