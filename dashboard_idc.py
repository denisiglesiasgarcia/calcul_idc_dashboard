# /dashboard_amoen.py

import os
import datetime
import pandas as pd
import streamlit as st
import matplotlib

matplotlib.use("Agg")

from sections.helpers.calcul_dj import (
    get_meteo_data,
)

from sections.helpers.rapport import (
    generate_pdf,
)

from sections.helpers.query_IDC import (
    make_request,
    convert_geometry_for_streamlit,
    show_map,
    show_dataframe,
    get_adresses_egid,
    create_barplot,
)

from sections.helpers.save_excel_streamlit import (
    display_dataframe_with_excel_download,
)

from sections.helpers.agents_energetiques import (
    display_agents_energetiques_idc,
)

from sections.helpers.dates import (
    display_dates_periode,
)

st.set_page_config(
    page_title="Outil Calcul IDC", page_icon=":bar_chart:", layout="wide"
)
os.environ["USE_ARROW_extension"] = "1"

# Variable pour la mise a jour de la météo
last_update_time_meteo = datetime.datetime(2021, 1, 1)

# IDC query
FIELDS = "*"
URL_INDICE_MOYENNES_3_ANS = "https://vector.sitg.ge.ch/arcgis/rest/services/Hosted/SCANE_INDICE_MOYENNES_3_ANS/FeatureServer/0/query"


if "data" not in st.session_state:
    st.session_state["data"] = {}


# Mise à jour météo
now = datetime.datetime.now()
if (now - last_update_time_meteo).days > 1:
    last_update_time_meteo = now
    st.session_state["df_meteo_tre200d0"] = get_meteo_data()


# dashboard
st.title("Outil de calcul de l'IDC")

# IDC théorie
st.subheader("Qu'est-ce que l'IDC")
st.write(
    "L'IDC (Indice de Dépense de Chaleur) est un \
    indicateur obligatoire de la consommation énergétique \
    des bâtiments genevois pour le chauffage et l'eau chaude. \
    Il doit être transmis annuellement à l'OCEN pour les\
    bâtiments de 5 preneurs de chaleur et plus.\
    Des mesures d'optimisation sont requises si\
    l'IDC dépasse 800 MJ/m²/an."
)

st.subheader("Sélection adresse")

# TODO: Create a multiselect for addresses

st.subheader("Plan de situation")

# TODO: Add a map to show the location of the site

st.subheader("Agents énérgétiques")

display_agents_energetiques_idc(st.session_state["data"])

# Subheader for the calculation period section
st.subheader("Période de calcul")

display_dates_periode()

st.subheader("Note de calcul")

# TODO: Note de calcul en latex

st.subheader("Résultats")

# TODO: Afficher les résultats

with tab2:

    @st.fragment
    def tab2_fragment():
        # projet
        st.subheader("Chargement données de base du projet")
        # in the database search unique values of the field 'nom_projet' in the documents mongodb
        nom_projets_liste = load_projets_liste(username)
        nom_projet_db = st.selectbox("Sélectionner projet", nom_projets_liste)

        data_sites_db = load_project_data(nom_projet_db)
        tab2_col01, tab2_col02 = st.columns(2)

        with tab2_col01:
            st.session_state["data_site"]["nom_projet"] = st.text_input(
                "Nom du projet", value=data_sites_db["nom_projet"]
            )
            # SRE rénovée
            sre_renovation_m2 = st.text_input(
                "SRE rénovée (m²):",
                value=round(data_sites_db["sre_renovation_m2"], 2),
                help="La SRE rénovée est la partie du batiment qui a été rénovée, la surélévation/extension n'est pas incluse",
            )
            validate_input("SRE rénovée:", sre_renovation_m2, "m²")
            st.session_state["data_site"]["sre_renovation_m2"] = float(
                sre_renovation_m2
            )
        with tab2_col02:
            st.session_state["data_site"]["adresse_projet"] = st.text_input(
                "Adresse(s) du projet", value=data_sites_db["adresse_projet"]
            )
            st.session_state["data_site"]["amoen_id"] = st.text_input(
                "AMOen", value=data_sites_db["amoen_id"]
            )

        try:
            if st.session_state["data_site"]["sre_renovation_m2"] <= 0:
                st.warning(
                    f"SRE doit être > 0 ({st.session_state['data_site']['sre_renovation_m2']})"
                )
        except ValueError:
            st.warning("Problème dans la somme des pourcentages des affectations")

        st.markdown(
            '<span style="font-size:1.2em;">**IDC moyen avant travaux et objectif en énergie finale**</span>',
            unsafe_allow_html=True,
        )
        # st.text("Ces données se trouvent dans le tableau Excel de fixation d'objectif de performances:\n\
        # - Surélévation: C92/C94\n\
        # - Rénovation: C61/C63")
        tab2_col5, tab2_col6 = st.columns(2)
        with tab2_col5:
            # Autres données
            # st.write('IDC moyen 3 ans avant travaux (Ef,avant,corr [kWh/m²/an])')
            ef_avant_corr_kwh_m2 = st.text_input(
                "IDC moyen 3 ans avant travaux (Ef,avant,corr [kWh/m²/an]):",
                value=round(data_sites_db["ef_avant_corr_kwh_m2"], 2),
                help="Surélévation: C92 / Rénovation: C61",
            )
            if ef_avant_corr_kwh_m2 != "0":
                validate_energie_input(
                    "Ef,avant,corr:", ef_avant_corr_kwh_m2, "kWh/m²/an", "MJ/m²/an"
                )
            st.session_state["data_site"]["ef_avant_corr_kwh_m2"] = float(
                ef_avant_corr_kwh_m2
            )
            try:
                if float(ef_avant_corr_kwh_m2) <= 0:
                    st.warning("Ef,avant,corr [kWh/m²/an] doit être supérieur à 0")
            except ValueError:
                st.warning("Problème dans Ef,avant,corr [kWh/m²/an]")

        with tab2_col6:
            ef_objectif_pondere_kwh_m2 = st.text_input(
                "Ef,obj * fp [kWh/m²/an]:",
                value=round(data_sites_db["ef_objectif_pondere_kwh_m2"], 2),
                help="Surélévation: C94 / Rénovation: C63",
            )
            if ef_objectif_pondere_kwh_m2 != "0":
                validate_energie_input(
                    "Ef,obj * fp:",
                    ef_objectif_pondere_kwh_m2,
                    "kWh/m²/an",
                    "MJ/m²/an",
                )
            st.session_state["data_site"]["ef_objectif_pondere_kwh_m2"] = float(
                ef_objectif_pondere_kwh_m2
            )
            try:
                if float(ef_objectif_pondere_kwh_m2) <= 0:
                    st.warning("Ef,obj *fp [kWh/m²/an] doit être supérieur à 0")
            except ValueError:
                st.warning("Problème dans Ef,obj *fp [kWh/m²/an]")

        st.markdown(
            '<span style="font-size:1.2em;">**Répartition énergie finale ECS/Chauffage**</span>',
            unsafe_allow_html=True,
        )

        tab2_col7, tab2_col8 = st.columns(2)
        with tab2_col7:
            # Répartition énergie finale
            # rénovation - chauffage
            repartition_energie_finale_partie_renovee_chauffage = st.text_input(
                "Chauffage partie rénovée [%]",
                value=round(
                    data_sites_db[
                        "repartition_energie_finale_partie_renovee_chauffage"
                    ],
                    2,
                ),
                help="Surélévation: C77 / Rénovation: C49",
            )
            if repartition_energie_finale_partie_renovee_chauffage != "0":
                validate_input(
                    "Répartition EF - Chauffage partie rénovée:",
                    repartition_energie_finale_partie_renovee_chauffage,
                    "%",
                )
            st.session_state["data_site"][
                "repartition_energie_finale_partie_renovee_chauffage"
            ] = float(repartition_energie_finale_partie_renovee_chauffage)
            # surélévation - chauffage
            repartition_energie_finale_partie_surelevee_chauffage = st.text_input(
                "Chauffage partie surélévée",
                value=round(
                    data_sites_db[
                        "repartition_energie_finale_partie_surelevee_chauffage"
                    ],
                    2,
                ),
                help="C79",
            )
            if repartition_energie_finale_partie_surelevee_chauffage != "0":
                validate_input(
                    "Répartition EF - Chauffage partie surélévée:",
                    repartition_energie_finale_partie_surelevee_chauffage,
                    "%",
                )
            st.session_state["data_site"][
                "repartition_energie_finale_partie_surelevee_chauffage"
            ] = float(repartition_energie_finale_partie_surelevee_chauffage)

        with tab2_col8:
            # rénovation - ECS
            repartition_energie_finale_partie_renovee_ecs = st.text_input(
                "ECS partie rénovée [%]",
                value=round(
                    data_sites_db["repartition_energie_finale_partie_renovee_ecs"],
                    2,
                ),
                help="Surélévation: C78 / Rénovation: C50",
            )
            if repartition_energie_finale_partie_renovee_ecs != "0":
                validate_input(
                    "Répartition EF - ECS partie rénovée:",
                    repartition_energie_finale_partie_renovee_ecs,
                    "%",
                )
            st.session_state["data_site"][
                "repartition_energie_finale_partie_renovee_ecs"
            ] = float(repartition_energie_finale_partie_renovee_ecs)
            # surélévation - ECS
            repartition_energie_finale_partie_surelevee_ecs = st.text_input(
                "ECS partie surélévée [%]",
                value=round(
                    data_sites_db["repartition_energie_finale_partie_surelevee_ecs"],
                    2,
                ),
                help="C80",
            )
            if repartition_energie_finale_partie_surelevee_ecs != "0":
                validate_input(
                    "Répartition EF - ECS partie surélevée:",
                    repartition_energie_finale_partie_surelevee_ecs,
                    "%",
                )
            st.session_state["data_site"][
                "repartition_energie_finale_partie_surelevee_ecs"
            ] = float(repartition_energie_finale_partie_surelevee_ecs)

        # Validation somme des pourcentages
        try:
            repartition_ef_somme_avertissement = (
                st.session_state["data_site"][
                    "repartition_energie_finale_partie_renovee_chauffage"
                ]
                + st.session_state["data_site"][
                    "repartition_energie_finale_partie_renovee_ecs"
                ]
                + st.session_state["data_site"][
                    "repartition_energie_finale_partie_surelevee_chauffage"
                ]
                + st.session_state["data_site"][
                    "repartition_energie_finale_partie_surelevee_ecs"
                ]
            )
            if repartition_ef_somme_avertissement != 100:
                st.warning(
                    f"La somme des pourcentages de répartition de l'énergie finale doit être égale à 100% ({repartition_ef_somme_avertissement}%)"
                )
        except ValueError:
            st.warning(
                "Problème dans la somme des pourcentages de répartition de l'énergie finale"
            )

        st.subheader("Eléments à renseigner", divider="rainbow")

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
                st.session_state["df_meteo_tre200d0"]["time"].max().strftime("%Y-%m-%d")
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

        st.session_state["data_site"]["periode_start"] = pd.to_datetime(periode_start)
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
            # Affectations SRE
            display_affectations(data_sites_db, sre_renovation_m2)

        with tab2_col2:
            # Agents énergétiques
            display_energy_agents(
                st.session_state["data_site"],
                data_sites_db,
            )

        # Autres données
        st.session_state["data_site"]["travaux_start"] = data_sites_db["travaux_start"]
        st.session_state["data_site"]["travaux_end"] = data_sites_db["travaux_end"]
        st.session_state["data_site"]["annees_calcul_idc_avant_travaux"] = (
            data_sites_db["annees_calcul_idc_avant_travaux"]
        )
        st.session_state["data_site"]["sre_extension_surelevation_m2"] = data_sites_db[
            "sre_extension_surelevation_m2"
        ]

    tab2_fragment()

    if st.button("Sauvegarder", use_container_width=True, type="primary"):
        st.success("Données validées")
        st.rerun()

    # Avusy spécifique
    if st.session_state["data_site"]["nom_projet"] == "Avusy 10-10A":
        st.divider()
        st.subheader("Informations spécifiques Avusy 10-10A")

        # Create tabs for different views
        avusy_tab1, avusy_tab2, avusy_tab3 = st.tabs(
            ["Dashboard", "Index des compteurs", "Mise à jour des données"]
        )

        with avusy_tab1:
            # Use the session state dates for the dashboard
            avusy_consommation_energie_dashboard(
                st.session_state["data_site"]["periode_start"],
                st.session_state["data_site"]["periode_end"],
                mycol_historique_index_avusy,
            )

        with avusy_tab2:
            display_counter_indices(mycol_historique_index_avusy)

        with avusy_tab3:
            update_existing_data_avusy(mycol_historique_index_avusy)

with tab3:
    st.subheader("Note de calcul")

    (
        df_periode_list,
        df_list,
        df_agent_energetique,
        df_meteo_note_calcul,
        df_results,
        formula_facteur_ponderation_moyen_texte,
        formula_facteur_ponderation_moyen,
    ) = fonction_note_calcul(
        st.session_state["data_site"], st.session_state["df_meteo_tre200d0"]
    )

    # Hide the index
    hide_index_style = """
        <style>
        thead tr th:first-child {display:none}
        tbody th {display:none}
        </style>
        """

    # Display the DataFrame in Streamlit without the index
    st.markdown(hide_index_style, unsafe_allow_html=True)

    # Display the dataframes
    st.write("Période sélectionnée")
    display_dataframe_with_excel_download(df_periode_list, "periode_liste.xlsx")

    st.write("Calculs effectués pour la période sélectionnée")
    display_dataframe_with_excel_download(df_list, "calculs_periode.xlsx")

    st.write("Agents énergétiques")
    display_dataframe_with_excel_download(
        df_agent_energetique, "agents_energetiques.xlsx"
    )

    # Render the text in LaTeX
    st.latex(formula_facteur_ponderation_moyen_texte)

    # Render the formula in LaTeX
    st.latex(formula_facteur_ponderation_moyen)

    # Display the meteo data
    st.write("Données météo station Genève-Cointrin pour la période sélectionnée")
    display_dataframe_with_excel_download(
        df_meteo_note_calcul, "meteo_note_calcul.xlsx"
    )

    # display a hidden dataframe with all the data
    st.write("Données complètes")
    show_debug_data = st.checkbox("Afficher les données complètes")
    if show_debug_data:
        display_dataframe_with_excel_download(
            st.session_state["data_site"], "data_site.xlsx"
        )
        display_dataframe_with_excel_download(
            st.session_state["df_meteo_tre200d0"], "df_meteo_tre200d0.xlsx"
        )

with tab4:
    st.subheader("Synthèse des résultats")
    if df_results is not None:
        st.table(df_results)
    else:
        st.warning(
            "Veuillez compléter les informations dans '1 Données site' pour voir les résultats"
        )

    # résultats en latex

    if (
        st.session_state["data_site"]["facteur_ponderation_moyen"] > 0
        and st.session_state["data_site"]["ef_avant_corr_kwh_m2"] > 0
        and st.session_state["data_site"][
            "energie_finale_apres_travaux_climatiquement_corrigee_renovee_pondere_kwh_m2"
        ]
        > 0
        and st.session_state["data_site"]["ef_objectif_pondere_kwh_m2"] > 0
        and st.session_state["data_site"]["atteinte_objectif"] > 0
    ):
        formula_atteinte_objectif = r"Atteinte\ objectif \ [\%]= \frac{{\Delta E_{{f,réel}}}}{{\Delta E_{{f,visée}}}} = \frac{{E_{{f,avant,corr}} - E_{{f,après,corr,rénové}}*f_{{p}}}}{{E_{{f,avant,corr}} - E_{{f,obj}}*f_{{p}}}}"

        formula_atteinte_objectif_num = r"Atteinte\ objectif \ [\%]= \frac{{{} - {}*{}}}{{{} - {}*{}}} = {}".format(
            round(st.session_state["data_site"]["ef_avant_corr_kwh_m2"], 4),
            round(
                st.session_state["data_site"][
                    "energie_finale_apres_travaux_climatiquement_corrigee_renovee_pondere_kwh_m2"
                ],
                4,
            )
            / round(st.session_state["data_site"]["facteur_ponderation_moyen"], 4),
            round(st.session_state["data_site"]["facteur_ponderation_moyen"], 4),
            round(st.session_state["data_site"]["ef_avant_corr_kwh_m2"], 4),
            round(st.session_state["data_site"]["ef_objectif_pondere_kwh_m2"], 4)
            / round(st.session_state["data_site"]["facteur_ponderation_moyen"], 4),
            round(st.session_state["data_site"]["facteur_ponderation_moyen"], 4),
            round(st.session_state["data_site"]["atteinte_objectif"], 3),
        )

        formula_atteinte_objectifs_pourcent = r"Atteinte\ objectif\ [\%]= {} \%".format(
            round(st.session_state["data_site"]["atteinte_objectif"] * 100, 2)
        )

        # latex color
        if st.session_state["data_site"]["atteinte_objectif"] >= 0.85:
            formula_atteinte_objectifs_pourcent = (
                r"\textcolor{green}{" + formula_atteinte_objectifs_pourcent + "}"
            )
        else:
            formula_atteinte_objectifs_pourcent = (
                r"\textcolor{red}{" + formula_atteinte_objectifs_pourcent + "}"
            )

        # Render the formula in LaTeX
        st.latex(formula_atteinte_objectif)
        st.latex(formula_atteinte_objectif_num)
        st.latex(formula_atteinte_objectifs_pourcent)

    st.subheader("Graphiques")

    # Graphique 1
    if (
        st.session_state["data_site"]["amoen_id"]
        and st.session_state["data_site"]["ef_avant_corr_kwh_m2"]
        and st.session_state["data_site"][
            "energie_finale_apres_travaux_climatiquement_corrigee_renovee_pondere_kwh_m2"
        ]
        and st.session_state["data_site"]["ef_objectif_pondere_kwh_m2"]
    ):
        graphique_bars_objectif_exploitation(
            st.session_state["data_site"]["nom_projet"],
            st.session_state["data_site"]["ef_avant_corr_kwh_m2"],
            st.session_state["data_site"][
                "energie_finale_apres_travaux_climatiquement_corrigee_renovee_pondere_kwh_m2"
            ],
            st.session_state["data_site"]["ef_objectif_pondere_kwh_m2"],
            st.session_state["data_site"]["atteinte_objectif"],
            st.session_state["data_site"]["amoen_id"],
        )
    else:
        st.warning(
            "Veuillez compléter les informations dans '1 Données site' pour générer le graphique"
        )

with tab5:
    # IDC
    # mulitselect adresses
    df_adresses_egid = get_adresses_egid()

    # Create a multiselect for addresses
    selected_addresses = st.session_state["data_site"]["adresse_projet"].split(";")

    if selected_addresses:
        # get egids that are selected
        filtered_df = df_adresses_egid[
            df_adresses_egid["adresse"].isin(selected_addresses)
        ]
        egids = filtered_df["egid"].tolist()

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
                geojson_data, centroid = convert_geometry_for_streamlit(data_geometry)
                show_map(geojson_data, centroid)

            st.subheader("Historique IDC")
            # create barplot
            create_barplot(data_df, st.session_state["data_site"]["nom_projet"])

            # show dataframe in something hidden like a
            if st.checkbox("Afficher les données IDC"):
                show_dataframe(data_df)
        else:
            st.error("Pas de données disponibles pour le(s) EGID associé(s) à ce site.")
    else:
        st.write("Pas d'adresse sélectionnée.")

    st.subheader("Historique résultats méthodologie AMOen")
    # get data from mongodb
    pipeline_historique_graphique = [
        {
            "$match": {
                "nom_projet": st.session_state["data_site"]["nom_projet"],
                "energie_finale_apres_travaux_climatiquement_corrigee_renovee_pondere_kwh_m2": {
                    "$ne": 0.0
                },
            }
        },
        {
            "$group": {
                "_id": {
                    "periode_start": "$periode_start",
                    "periode_end": "$periode_end",
                },
                "doc": {"$first": "$$ROOT"},
            }
        },
        {"$replaceRoot": {"newRoot": "$doc"}},
    ]
    # Execute the aggregation pipeline
    data_db_historique = mycol_historique_sites.aggregate(pipeline_historique_graphique)

    # Process the results
    if data_db_historique:
        data_list = list(data_db_historique)

        # Convert to DataFrame
        df_historique_complet = pd.DataFrame(data_list)

        # Ensure required columns are present
        required_columns = [
            "nom_projet",
            "periode_start",
            "periode_end",
            "atteinte_objectif",
        ]

        # Proceed only if all required columns are present
        if all([col in df_historique_complet.columns for col in required_columns]):
            create_barplot_historique_amoen(df_historique_complet)

            # Show DataFrame in a hidden section
            if st.checkbox("Afficher les données historiques"):
                display_dataframe_with_excel_download(
                    df_historique_complet, "historique_amoen.xlsx"
                )
        else:
            st.error("Pas de données historiques disponibles")

with tab6:
    st.subheader("Générer rapport")

    # Check if all fields are valid
    def is_valid(var):
        """
        Check if a variable is valid.

        A variable is considered valid if it is not None and not an empty string.

        Args:
            var: The variable to check.

        Returns:
            bool: True if the variable is valid, False otherwise.
        """
        return var is not None and var != ""

    def check_validity():
        """
        Checks the validity of various fields in the session state data.

        This function iterates over a predefined list of fields and checks if each field
        in the session state data is valid. If a field is found to be invalid, it is added
        to a list of invalid fields.

        Returns:
            list: A list of field names that are invalid.
        """
        invalid_fields = []
        fields_to_check = [
            "nom_projet",
            "adresse_projet",
            "amoen_id",
            "sre_renovation_m2",
            "sre_pourcentage_habitat_collectif",
            "sre_pourcentage_habitat_individuel",
            "sre_pourcentage_administration",
            "sre_pourcentage_ecoles",
            "sre_pourcentage_commerce",
            "sre_pourcentage_restauration",
            "sre_pourcentage_lieux_de_rassemblement",
            "sre_pourcentage_hopitaux",
            "sre_pourcentage_industrie",
            "sre_pourcentage_depots",
            "sre_pourcentage_installations_sportives",
            "sre_pourcentage_piscines_couvertes",
            "agent_energetique_ef_mazout_kg",
            "agent_energetique_ef_mazout_litres",
            "agent_energetique_ef_mazout_kwh",
            "agent_energetique_ef_gaz_naturel_m3",
            "agent_energetique_ef_gaz_naturel_kwh",
            "agent_energetique_ef_bois_buches_dur_stere",
            "agent_energetique_ef_bois_buches_tendre_stere",
            "agent_energetique_ef_bois_buches_tendre_kwh",
            "agent_energetique_ef_pellets_m3",
            "agent_energetique_ef_pellets_kg",
            "agent_energetique_ef_pellets_kwh",
            "agent_energetique_ef_plaquettes_m3",
            "agent_energetique_ef_plaquettes_kwh",
            "agent_energetique_ef_cad_kwh",
            "agent_energetique_ef_electricite_pac_kwh",
            "agent_energetique_ef_electricite_directe_kwh",
            "agent_energetique_ef_autre_kwh",
            "periode_start",
            "periode_end",
            "ef_avant_corr_kwh_m2",
            "ef_objectif_pondere_kwh_m2",
            "energie_finale_apres_travaux_climatiquement_corrigee_renovee_pondere_kwh_m2",
            "delta_ef_visee_kwh_m2",
            "facteur_ponderation_moyen",
            "atteinte_objectif",
            "repartition_energie_finale_partie_renovee_chauffage",
            "repartition_energie_finale_partie_renovee_ecs",
            "repartition_energie_finale_partie_surelevee_chauffage",
            "repartition_energie_finale_partie_surelevee_ecs",
        ]

        for field in fields_to_check:
            if not is_valid(st.session_state["data_site"].get(field)):
                invalid_fields.append(field)

        return invalid_fields

    # Generate the PDF report
    invalid_fields = check_validity()
    if not invalid_fields:
        if st.button("Générer le rapport PDF"):
            pdf_data, file_name = generate_pdf(st.session_state["data_site"])
            st.download_button(
                label="Cliquez ici pour télécharger le PDF",
                data=pdf_data,
                file_name=file_name,
                mime="application/pdf",
            )
            st.success(
                f"Rapport PDF '{file_name}' généré avec succès! Cliquez sur le bouton ci-dessus pour le télécharger."
            )

            # add date to data_rapport
            st.session_state["data_site"][
                "date_rapport"
            ] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Remove the _id field if it exists to ensure MongoDB generates a new one
            if "_id" in st.session_state["data_site"]:
                del st.session_state["data_site"]["_id"]

            # Send data_site to MongoDB
            x = mycol_historique_sites.insert_one(st.session_state["data_site"])
    else:
        st.warning(
            "Toutes les informations nécessaires ne sont pas disponibles pour générer le PDF."
        )
        invalid_fields_list = "\n".join([f"- {field}" for field in invalid_fields])
        st.warning(
            f"Les champs suivants sont invalides ou manquants:\n\n{invalid_fields_list}"
        )
