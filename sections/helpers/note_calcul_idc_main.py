# sections/note_calcul.py

# import pandas as pd
# import streamlit as st

from sections.helpers.note_calcul.create_dataframe_periode_list import (
    make_dataframe_df_periode_list,
)

from sections.helpers.note_calcul.create_dataframe_idc import (
    make_dataframe_df_list_idc,
    make_dataframe_df_agent_energetique_idc,
    )

from sections.helpers.note_calcul.create_dataframe_meteo import (
    make_dataframe_df_meteo_note_calcul,
)

from sections.helpers.note_calcul.create_dataframe_results import (
    make_dataframe_df_results,
)


from sections.helpers.calcul_dj import (
    calcul_dj_periode,
)

from sections.helpers.note_calcul.calculs_idc import (
    fonction_idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2,
    fonction_idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj,
    fonction_idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj,
    fonction_idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2,
    fonction_idc_bh_energie_finale_chauffage_comptage_ecs_inclus_mj,
    fonction_idc_bh_energie_finale_chauffage_comptage_ecs_non_inclus_mj,
    fonction_idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_inclus_mj_m2,
    fonction_idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_non_inclus_mj_m2,
    fonction_idc_resultat_comptage_ecs_inclus_mj_m2,
    fonction_idc_resultat_comptage_ecs_non_inclus_mj_m2,
    fonction_conversion_energie_idc,
)

from sections.helpers.note_calcul.constantes import (
    DJ_REF_ANNUELS,
    IDC_CONVERSION_MAZOUT_MJ_KG,
    IDC_CONVERSION_MAZOUT_MJ_LITRES,
    IDC_CONVERSION_MAZOUT_MJ_KWH,
    IDC_CONVERSION_GAZ_NATUREL_MJ_M3,
    IDC_CONVERSION_GAZ_NATUREL_MJ_KWH,
    IDC_CONVERSION_BOIS_BUCHES_DUR_MJ_STERE,
    IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_STERE,
    IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_KWH,
    IDC_CONVERSION_PELLETS_MJ_M3,
    IDC_CONVERSION_PELLETS_MJ_KG,
    IDC_CONVERSION_PELLETS_MJ_KWH,
    IDC_CONVERSION_PLAQUETTES_MJ_M3,
    IDC_CONVERSION_PLAQUETTES_MJ_KWH,
    IDC_CONVERSION_CAD_TARIFE_MJ_KWH,
    IDC_CONVERSION_CAD_REPARTI_MJ_KWH,
    IDC_CONVERSION_ELECTRICITE_PAC_AVANT_MJ_KWH,
    IDC_CONVERSION_ELECTRICITE_PAC_APRES_MJ_KWH,
    IDC_CONVERSION_ELECTRICITE_DIRECTE_MJ_KWH,
    IDC_CONVERSION_AUTRE_MJ_KWH,
    IDC_FACTEUR_PONDERATION_MAZOUT,
    IDC_FACTEUR_PONDERATION_GAZ_NATUREL,
    IDC_FACTEUR_PONDERATION_BOIS_BUCHES_DUR,
    IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE,
    IDC_FACTEUR_PONDERATION_PELLETS,
    IDC_FACTEUR_PONDERATION_PLAQUETTES,
    IDC_FACTEUR_PONDERATION_CAD,
    IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_AVANT,
    IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_APRES,
    IDC_FACTEUR_PONDERATION_ELECTRICITE_DIRECTE,
    IDC_FACTEUR_PONDERATION_AUTRE,
    IDC_EWW_HABITAT_COLLECTIF_MJ_M2,
    IDC_EWW_HABITAT_INDIVIDUEL_MJ_M2,
    IDC_EWW_ADMINISTRATION_MJ_M2,
    IDC_EWW_ECOLES_MJ_M2,
    IDC_EWW_COMMERCE_MJ_M2,
    IDC_EWW_RESTAURATION_MJ_M2,
    IDC_EWW_LIEUX_DE_RASSEMBLEMENT_MJ_M2,
    IDC_EWW_HOPITAUX_MJ_M2,
    IDC_EWW_INDUSTRIE_MJ_M2,
    IDC_EWW_DEPOTS_MJ_M2,
    IDC_EWW_INSTALLATIONS_SPORTIVES_MJ_M2,
    IDC_EWW_PISCINES_COUVERTES_MJ_M2
)

import pandas as pd
import streamlit as st


def fonction_note_calcul_idc(data_site, df_meteo_tre200d0):
    """
    Calculates various energy-related metrics for a given site based on input data.
    This function processes energy consumption data for a site, calculates degree days,
    and computes energy metrics for heating and domestic hot water (ECS) based on whether
    ECS metering is included or not. It also handles potential errors during calculations
    and ensures that all required metrics are initialized.
    Parameters:
        data_site (dict): A dictionary containing site-specific data. Expected keys include:
            - "periode_start" (str): Start date of the period in "YYYY-MM-DD" format.
            - "periode_end" (str): End date of the period in "YYYY-MM-DD" format.
            - "periode_nb_jours" (int): Number of days in the period.
            - "idc_sre_m2" (float): Surface area in square meters.
            - "sre_pourcentage_*" (float): Percentages of different building types (e.g., habitat_collectif, habitat_individuel, etc.).
            - "comptage_ecs_inclus" (bool): Whether ECS metering is included.
            - "sre_pourcentage_habitat_collectif"
            - "sre_pourcentage_habitat_individuel"
            - "sre_pourcentage_administration"
            - "sre_pourcentage_ecoles"
            - "sre_pourcentage_commerce"
            - "sre_pourcentage_restauration"
            - "sre_pourcentage_lieux_de_rassemblement"
            - "sre_pourcentage_hopitaux"
            - "sre_pourcentage_industrie"
            - "sre_pourcentage_depots"
            - "sre_pourcentage_installations_sportives"
            - "sre_pourcentage_piscines_couvertes"
            - "sre_pourcentage_autre"

        df_meteo_tre200d0 (pd.DataFrame): A DataFrame containing meteorological data with at least:
            - "time" (datetime): Timestamps for the meteorological data.
    Returns:
        None: Updates the `data_site` dictionary in place with the following keys:
            - "dj_periode" (float): Degree days for the specified period.
            - "idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2" (float): Theoretical average ECS energy consumption (MJ/m²).
            - "idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj" (float): Final ECS energy consumption (MJ).
            - "idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj" (float): Final ECS energy consumption without metering (MJ).
            - "idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2" (float): ECS energy consumption per m² without metering (MJ/m²).
            - "idc_bh_energie_finale_chauffage_comptage_ecs_inclus_mj" (float): Final heating energy consumption with metering (MJ).
            - "idc_bh_energie_finale_chauffage_comptage_ecs_non_inclus_mj" (float): Final heating energy consumption without metering (MJ).
            - "idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_inclus_mj_m2" (float): Climate-corrected heating energy consumption per m² with metering (MJ/m²).
            - "idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_non_inclus_mj_m2" (float): Climate-corrected heating energy consumption per m² without metering (MJ/m²).
            - "idc_resultat_comptage_ecs_inclus_mj_m2" (float): Final energy result with metering (MJ/m²).
            - "idc_resultat_comptage_ecs_non_inclus_mj_m2" (float): Final energy result without metering (MJ/m²).
    Raises:
        Exception: If any error occurs during calculations, it initializes all metrics to 0
                   and logs the error message.
    Notes:
        - The function ensures that "periode_start" and "periode_end" are properly formatted
          and compatible with the meteorological data.
        - Degree days are calculated using the `calcul_dj_periode` function.
        - Energy metrics are computed using various helper functions (e.g., `fonction_idc_*`).
        - If ECS metering is included, separate calculations are performed for heating and ECS.
        - If ECS metering is not included, combined calculations are performed for heating and ECS.
        - In case of errors, all metrics are set to 0 to avoid further issues.
    """

    # Ensure periode_start and periode_end are in the correct format for comparison
    try:
        # Explicitly convert periode_start and periode_end to the same format as df_meteo_tre200d0["time"]
        periode_start = pd.to_datetime(data_site["periode_start"]).strftime("%Y-%m-%d")
        periode_end = pd.to_datetime(data_site["periode_end"]).strftime("%Y-%m-%d")
        
        # Convert dates back to pandas datetime objects
        periode_start = pd.to_datetime(periode_start)
        periode_end = pd.to_datetime(periode_end)

        # Calculate degree days
        data_site["dj_periode"] = calcul_dj_periode(
            df_meteo_tre200d0,
            periode_start,
            periode_end,
        )
        
        # Convert to float and add validation
        data_site["dj_periode"] = float(data_site["dj_periode"])
        
        # Validate result
        if data_site["dj_periode"] <= 0:
            st.warning(f"Le calcul des degrés-jours a retourné une valeur nulle ou négative: {data_site['dj_periode']}. Veuillez vérifier les dates choisies.")
            # Still set a minimum value to avoid division by zero errors
            data_site["dj_periode"] = 0.1
    except Exception as e:
        # Set dj_periode to a small non-zero value to avoid division by zero
        data_site["dj_periode"] = 0.1
        # Show error to user
        error_message = f"Erreur lors du calcul des degrés-jours: {str(e)}"
        st.error(error_message)
        print(error_message)

    # IDC
    try:
        # cas comptage ECS inclus
        if data_site["comptage_ecs_inclus"]:
            # ECS
            # C119
            data_site["idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2"] = fonction_idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2(
                data_site["sre_pourcentage_habitat_collectif"],
                data_site["sre_pourcentage_habitat_individuel"],
                data_site["sre_pourcentage_administration"],
                data_site["sre_pourcentage_ecoles"],
                data_site["sre_pourcentage_commerce"],
                data_site["sre_pourcentage_restauration"],
                data_site["sre_pourcentage_lieux_de_rassemblement"],
                data_site["sre_pourcentage_hopitaux"],
                data_site["sre_pourcentage_industrie"],
                data_site["sre_pourcentage_depots"],
                data_site["sre_pourcentage_installations_sportives"],
                data_site["sre_pourcentage_piscines_couvertes"],
                IDC_EWW_HABITAT_COLLECTIF_MJ_M2,
                IDC_EWW_HABITAT_INDIVIDUEL_MJ_M2,
                IDC_EWW_ADMINISTRATION_MJ_M2,
                IDC_EWW_ECOLES_MJ_M2,
                IDC_EWW_COMMERCE_MJ_M2,
                IDC_EWW_RESTAURATION_MJ_M2,
                IDC_EWW_LIEUX_DE_RASSEMBLEMENT_MJ_M2,
                IDC_EWW_HOPITAUX_MJ_M2,
                IDC_EWW_INDUSTRIE_MJ_M2,
                IDC_EWW_DEPOTS_MJ_M2,
                IDC_EWW_INSTALLATIONS_SPORTIVES_MJ_M2,
                IDC_EWW_PISCINES_COUVERTES_MJ_M2,
            )
            # C118
            data_site["idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj"] = fonction_idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj(
                data_site["idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2"],
                data_site["idc_sre_m2"],
                data_site["periode_nb_jours"],
                )
           
            # Chauffage
            # C120
            data_site["idc_bh_energie_finale_chauffage_comptage_ecs_inclus_mj"] = fonction_idc_bh_energie_finale_chauffage_comptage_ecs_inclus_mj(
                data_site["idc_agent_energetique_ef_cad_reparti_kwh"],
                data_site["idc_agent_energetique_ef_cad_tarife_kwh"],
                data_site["idc_agent_energetique_ef_electricite_pac_avant_kwh"],
                data_site["idc_agent_energetique_ef_electricite_pac_apres_kwh"],
                data_site["idc_agent_energetique_ef_electricite_directe_kwh"],
                data_site["idc_agent_energetique_ef_gaz_naturel_m3"],
                data_site["idc_agent_energetique_ef_gaz_naturel_kwh"],
                data_site["idc_agent_energetique_ef_mazout_litres"],
                data_site["idc_agent_energetique_ef_mazout_kg"],
                data_site["idc_agent_energetique_ef_mazout_kwh"],
                data_site["idc_agent_energetique_ef_bois_buches_dur_stere"],
                data_site["idc_agent_energetique_ef_bois_buches_tendre_stere"],
                data_site["idc_agent_energetique_ef_bois_buches_tendre_kwh"],
                data_site["idc_agent_energetique_ef_pellets_m3"],
                data_site["idc_agent_energetique_ef_pellets_kg"],
                data_site["idc_agent_energetique_ef_pellets_kwh"],
                data_site["idc_agent_energetique_ef_plaquettes_m3"],
                data_site["idc_agent_energetique_ef_plaquettes_kwh"],
                data_site["idc_agent_energetique_ef_autre_kwh"],
                IDC_CONVERSION_CAD_REPARTI_MJ_KWH,
                IDC_CONVERSION_CAD_TARIFE_MJ_KWH,
                IDC_CONVERSION_ELECTRICITE_PAC_AVANT_MJ_KWH,
                IDC_CONVERSION_ELECTRICITE_PAC_APRES_MJ_KWH,
                IDC_CONVERSION_ELECTRICITE_DIRECTE_MJ_KWH,
                IDC_CONVERSION_GAZ_NATUREL_MJ_M3,
                IDC_CONVERSION_GAZ_NATUREL_MJ_KWH,
                IDC_CONVERSION_MAZOUT_MJ_LITRES,
                IDC_CONVERSION_MAZOUT_MJ_KG,
                IDC_CONVERSION_MAZOUT_MJ_KWH,
                IDC_CONVERSION_BOIS_BUCHES_DUR_MJ_STERE,
                IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_STERE,
                IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_KWH,
                IDC_CONVERSION_PELLETS_MJ_M3,
                IDC_CONVERSION_PELLETS_MJ_KG,
                IDC_CONVERSION_PELLETS_MJ_KWH,
                IDC_CONVERSION_PLAQUETTES_MJ_M3,
                IDC_CONVERSION_PLAQUETTES_MJ_KWH,
                IDC_CONVERSION_AUTRE_MJ_KWH,
                IDC_FACTEUR_PONDERATION_CAD,
                IDC_FACTEUR_PONDERATION_GAZ_NATUREL,
                IDC_FACTEUR_PONDERATION_BOIS_BUCHES_DUR,
                IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE,
                IDC_FACTEUR_PONDERATION_PELLETS,
                IDC_FACTEUR_PONDERATION_PLAQUETTES,
                IDC_FACTEUR_PONDERATION_MAZOUT,
                IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_AVANT,
                IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_APRES,
                IDC_FACTEUR_PONDERATION_ELECTRICITE_DIRECTE,
                IDC_FACTEUR_PONDERATION_AUTRE,
                data_site["idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj"],
                )
            # C123
            data_site["idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_inclus_mj_m2"] = fonction_idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_inclus_mj_m2(
                data_site["idc_bh_energie_finale_chauffage_comptage_ecs_inclus_mj"],
                data_site["idc_sre_m2"],
                DJ_REF_ANNUELS,
                data_site["dj_periode"],
                )
            # Total
            # C124
            data_site["idc_resultat_comptage_ecs_inclus_mj_m2"] = fonction_idc_resultat_comptage_ecs_inclus_mj_m2(
                data_site["idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_inclus_mj_m2"],
                data_site["idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2"],
                )
            
            # Variante ECS séparé
            data_site["idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj"] = 0
            data_site["idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2"] = 0
            data_site["idc_bh_energie_finale_chauffage_comptage_ecs_non_inclus_mj"] = 0
            data_site["idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_non_inclus_mj_m2"] = 0
            data_site["idc_resultat_comptage_ecs_non_inclus_mj_m2"] = 0
            data_site["idc_ecs_agent_energetique_ef_cad_reparti_kwh"] = 0
            data_site["idc_ecs_agent_energetique_ef_cad_tarife_kwh"] = 0
            data_site["idc_ecs_agent_energetique_ef_electricite_pac_avant_kwh"] = 0
            data_site["idc_ecs_agent_energetique_ef_electricite_pac_apres_kwh"] = 0
            data_site["idc_ecs_agent_energetique_ef_electricite_directe_kwh"] = 0
            data_site["idc_ecs_agent_energetique_ef_gaz_naturel_m3"] = 0
            data_site["idc_ecs_agent_energetique_ef_gaz_naturel_kwh"] = 0
            data_site["idc_ecs_agent_energetique_ef_mazout_litres"] = 0
            data_site["idc_ecs_agent_energetique_ef_mazout_kg"] = 0
            data_site["idc_ecs_agent_energetique_ef_mazout_kwh"] = 0
            data_site["idc_ecs_agent_energetique_ef_bois_buches_dur_stere"] = 0
            data_site["idc_ecs_agent_energetique_ef_bois_buches_tendre_stere"] = 0
            data_site["idc_ecs_agent_energetique_ef_bois_buches_tendre_kwh"] = 0
            data_site["idc_ecs_agent_energetique_ef_pellets_m3"] = 0
            data_site["idc_ecs_agent_energetique_ef_pellets_kg"] = 0
            data_site["idc_ecs_agent_energetique_ef_pellets_kwh"] = 0
            data_site["idc_ecs_agent_energetique_ef_plaquettes_m3"] = 0
            data_site["idc_ecs_agent_energetique_ef_plaquettes_kwh"] = 0
            data_site["idc_ecs_agent_energetique_ef_autre_kwh"] = 0

        # cas comptage ECS pas inclus
        else:
            # ECS
            # C118
            data_site["idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj"] = fonction_idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj(
                data_site["idc_ecs_agent_energetique_ef_cad_reparti_kwh"],
                data_site["idc_ecs_agent_energetique_ef_cad_tarife_kwh"],
                data_site["idc_ecs_agent_energetique_ef_electricite_pac_avant_kwh"],
                data_site["idc_ecs_agent_energetique_ef_electricite_pac_apres_kwh"],
                data_site["idc_ecs_agent_energetique_ef_electricite_directe_kwh"],
                data_site["idc_ecs_agent_energetique_ef_gaz_naturel_m3"],
                data_site["idc_ecs_agent_energetique_ef_gaz_naturel_kwh"],
                data_site["idc_ecs_agent_energetique_ef_mazout_litres"],
                data_site["idc_ecs_agent_energetique_ef_mazout_kg"],
                data_site["idc_ecs_agent_energetique_ef_mazout_kwh"],
                data_site["idc_ecs_agent_energetique_ef_bois_buches_dur_stere"],
                data_site["idc_ecs_agent_energetique_ef_bois_buches_tendre_stere"],
                data_site["idc_ecs_agent_energetique_ef_bois_buches_tendre_kwh"],
                data_site["idc_ecs_agent_energetique_ef_pellets_m3"],
                data_site["idc_ecs_agent_energetique_ef_pellets_kg"],
                data_site["idc_ecs_agent_energetique_ef_pellets_kwh"],
                data_site["idc_ecs_agent_energetique_ef_plaquettes_m3"],
                data_site["idc_ecs_agent_energetique_ef_plaquettes_kwh"],
                data_site["idc_ecs_agent_energetique_ef_autre_kwh"],
                IDC_CONVERSION_CAD_REPARTI_MJ_KWH,
                IDC_CONVERSION_CAD_TARIFE_MJ_KWH,
                IDC_CONVERSION_ELECTRICITE_PAC_AVANT_MJ_KWH,
                IDC_CONVERSION_ELECTRICITE_PAC_APRES_MJ_KWH,
                IDC_CONVERSION_ELECTRICITE_DIRECTE_MJ_KWH,
                IDC_CONVERSION_GAZ_NATUREL_MJ_M3,
                IDC_CONVERSION_GAZ_NATUREL_MJ_KWH,
                IDC_CONVERSION_MAZOUT_MJ_LITRES,
                IDC_CONVERSION_MAZOUT_MJ_KG,
                IDC_CONVERSION_MAZOUT_MJ_KWH,
                IDC_CONVERSION_BOIS_BUCHES_DUR_MJ_STERE,
                IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_STERE,
                IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_KWH,
                IDC_CONVERSION_PELLETS_MJ_M3,
                IDC_CONVERSION_PELLETS_MJ_KG,
                IDC_CONVERSION_PELLETS_MJ_KWH,
                IDC_CONVERSION_PLAQUETTES_MJ_M3,
                IDC_CONVERSION_PLAQUETTES_MJ_KWH,
                IDC_CONVERSION_AUTRE_MJ_KWH,
                IDC_FACTEUR_PONDERATION_CAD,
                IDC_FACTEUR_PONDERATION_GAZ_NATUREL,
                IDC_FACTEUR_PONDERATION_BOIS_BUCHES_DUR,
                IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE,
                IDC_FACTEUR_PONDERATION_PELLETS,
                IDC_FACTEUR_PONDERATION_PLAQUETTES,
                IDC_FACTEUR_PONDERATION_MAZOUT,
                IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_AVANT,
                IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_APRES,
                IDC_FACTEUR_PONDERATION_ELECTRICITE_DIRECTE,
                IDC_FACTEUR_PONDERATION_AUTRE,
                )
            
            # C119
            data_site["idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2"] = fonction_idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2(
                data_site["idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj"],
                data_site["idc_sre_m2"])
            
            # Chauffage
            data_site["idc_bh_energie_finale_chauffage_comptage_ecs_non_inclus_mj"] = fonction_idc_bh_energie_finale_chauffage_comptage_ecs_non_inclus_mj(
                data_site["idc_ecs_agent_energetique_ef_cad_reparti_kwh"],
                data_site["idc_ecs_agent_energetique_ef_cad_tarife_kwh"],
                data_site["idc_ecs_agent_energetique_ef_electricite_pac_avant_kwh"],
                data_site["idc_ecs_agent_energetique_ef_electricite_pac_apres_kwh"],
                data_site["idc_ecs_agent_energetique_ef_electricite_directe_kwh"],
                data_site["idc_ecs_agent_energetique_ef_gaz_naturel_m3"],
                data_site["idc_ecs_agent_energetique_ef_gaz_naturel_kwh"],
                data_site["idc_ecs_agent_energetique_ef_mazout_litres"],
                data_site["idc_ecs_agent_energetique_ef_mazout_kg"],
                data_site["idc_ecs_agent_energetique_ef_mazout_kwh"],
                data_site["idc_ecs_agent_energetique_ef_bois_buches_dur_stere"],
                data_site["idc_ecs_agent_energetique_ef_bois_buches_tendre_stere"],
                data_site["idc_ecs_agent_energetique_ef_bois_buches_tendre_kwh"],
                data_site["idc_ecs_agent_energetique_ef_pellets_m3"],
                data_site["idc_ecs_agent_energetique_ef_pellets_kg"],
                data_site["idc_ecs_agent_energetique_ef_pellets_kwh"],
                data_site["idc_ecs_agent_energetique_ef_plaquettes_m3"],
                data_site["idc_ecs_agent_energetique_ef_plaquettes_kwh"],
                data_site["idc_ecs_agent_energetique_ef_autre_kwh"],
                IDC_CONVERSION_CAD_REPARTI_MJ_KWH,
                IDC_CONVERSION_CAD_TARIFE_MJ_KWH,
                IDC_CONVERSION_ELECTRICITE_PAC_AVANT_MJ_KWH,
                IDC_CONVERSION_ELECTRICITE_PAC_APRES_MJ_KWH,
                IDC_CONVERSION_ELECTRICITE_DIRECTE_MJ_KWH,
                IDC_CONVERSION_GAZ_NATUREL_MJ_M3,
                IDC_CONVERSION_GAZ_NATUREL_MJ_KWH,
                IDC_CONVERSION_MAZOUT_MJ_LITRES,
                IDC_CONVERSION_MAZOUT_MJ_KG,
                IDC_CONVERSION_MAZOUT_MJ_KWH,
                IDC_CONVERSION_BOIS_BUCHES_DUR_MJ_STERE,
                IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_STERE,
                IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_KWH,
                IDC_CONVERSION_PELLETS_MJ_M3,
                IDC_CONVERSION_PELLETS_MJ_KG,
                IDC_CONVERSION_PELLETS_MJ_KWH,
                IDC_CONVERSION_PLAQUETTES_MJ_M3,
                IDC_CONVERSION_PLAQUETTES_MJ_KWH,
                IDC_CONVERSION_AUTRE_MJ_KWH,
                IDC_FACTEUR_PONDERATION_CAD,
                IDC_FACTEUR_PONDERATION_GAZ_NATUREL,
                IDC_FACTEUR_PONDERATION_BOIS_BUCHES_DUR,
                IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE,
                IDC_FACTEUR_PONDERATION_PELLETS,
                IDC_FACTEUR_PONDERATION_PLAQUETTES,
                IDC_FACTEUR_PONDERATION_MAZOUT,
                IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_AVANT,
                IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_APRES,
                IDC_FACTEUR_PONDERATION_ELECTRICITE_DIRECTE,
                IDC_FACTEUR_PONDERATION_AUTRE,
                data_site["idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj"]
                )

            data_site["idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_non_inclus_mj_m2"] = fonction_idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_non_inclus_mj_m2(
                data_site["idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2"],
                data_site["idc_sre_m2"],
                DJ_REF_ANNUELS,
                data_site["dj_periode"]
            )
            # Total
            data_site["idc_resultat_comptage_ecs_non_inclus_mj_m2"] = fonction_idc_resultat_comptage_ecs_non_inclus_mj_m2(
                data_site["idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_non_inclus_mj_m2"],
                data_site["idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2"],
            )
            
            # Variante ECS intégré
            data_site["idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2"] = 0
            data_site["idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj"] = 0
            data_site["idc_eww_part_energie_finale_ecs_comptage_ecs_inclus_mj_m2"] = 0
            data_site["idc_bh_energie_finale_chauffage_comptage_ecs_inclus_mj"] = 0
            data_site["idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_inclus_mj_m2"] = 0
            data_site["idc_resultat_comptage_ecs_inclus_mj_m2"] = 0

    except Exception as e:
        print("error", e)
        # ECS
        data_site["idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2"] = 0
        data_site["idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj"] = 0
        data_site["idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj"] = 0
        data_site["idc_eww_part_energie_finale_ecs_comptage_ecs_inclus_mj_m2"] = 0
        data_site["idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2"] = 0
        # Chauffage
        data_site["idc_bh_energie_finale_chauffage_comptage_ecs_inclus_mj"] = 0
        data_site["idc_bh_energie_finale_chauffage_comptage_ecs_non_inclus_mj"] = 0
        data_site["idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_inclus_mj_m2"] = 0
        data_site["idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_non_inclus_mj_m2"] = 0
        # Total
        data_site["idc_resultat_comptage_ecs_inclus_mj_m2"] = 0
        data_site["idc_resultat_comptage_ecs_non_inclus_mj_m2"] = 0
    
    return data_site
    
def fonction_note_calcul_idc_dataframe(data_site, df_meteo_tre200d0):
    """
    Generates various dataframes and performs energy conversion calculations 
    for the IDC (Indice de Consommation) dashboard.
    Args:
        data_site (dict): A dictionary containing site-specific data, including 
            energy consumption and period information. Expected keys include:
            - "periode_start": Start date of the period.
            - "periode_end": End date of the period.
            - Various energy consumption metrics (e.g., kWh, m3, liters, etc.).
        df_meteo_tre200d0 (pd.DataFrame): A DataFrame containing meteorological 
            data for the specified period.
    Returns:
        tuple: A tuple containing the following dataframes:
            - df_periode_list (pd.DataFrame): DataFrame representing the list 
              of periods.
            - df_list_idc (pd.DataFrame): DataFrame containing IDC-related 
              metrics.
            - df_agent_energetique_idc_sum (pd.DataFrame): DataFrame summarizing 
              energy consumption by energy source.
            - df_agent_energetique_idc_mazout (pd.DataFrame): DataFrame for 
              mazout energy consumption.
            - df_agent_energetique_idc_gaz_naturel (pd.DataFrame): DataFrame for 
              natural gas energy consumption.
            - df_agent_energetique_idc_bois_buches_dur (pd.DataFrame): DataFrame 
              for hardwood logs energy consumption.
            - df_agent_energetique_idc_bois_buches_tendre (pd.DataFrame): 
              DataFrame for softwood logs energy consumption.
            - df_agent_energetique_idc_pellets (pd.DataFrame): DataFrame for 
              pellets energy consumption.
            - df_agent_energetique_idc_plaquettes (pd.DataFrame): DataFrame for 
              wood chips energy consumption.
            - df_agent_energetique_idc_cad_reparti (pd.DataFrame): DataFrame for 
              district heating (repartition) energy consumption.
            - df_agent_energetique_idc_cad_tarife (pd.DataFrame): DataFrame for 
              district heating (tariff) energy consumption.
            - df_agent_energetique_idc_electricite_pac_avant (pd.DataFrame): 
              DataFrame for electricity consumption by heat pumps (before).
            - df_agent_energetique_idc_electricite_pac_apres (pd.DataFrame): 
              DataFrame for electricity consumption by heat pumps (after).
            - df_agent_energetique_idc_electricite_directe (pd.DataFrame): 
              DataFrame for direct electricity consumption.
            - df_agent_energetique_idc_autre (pd.DataFrame): DataFrame for 
              other energy sources.
    Raises:
        Exception: If an error occurs during the creation of the meteorological 
        DataFrame for degree-day calculations.
    Notes:
        - This function relies on several helper functions, such as 
          `make_dataframe_df_periode_list`, `make_dataframe_df_meteo_note_calcul`, 
          `fonction_conversion_energie_idc`, and 
          `make_dataframe_df_agent_energetique_idc`.
        - The function performs energy conversion calculations using various 
          constants (e.g., IDC_CONVERSION_* and IDC_FACTEUR_PONDERATION_*).
    """
    # df_periode_list
    df_periode_list = make_dataframe_df_periode_list(
        data_site["periode_start"], data_site["periode_end"]
    )
    
    # météo
    try:
        df_meteo_tre200d0 = make_dataframe_df_meteo_note_calcul(
            data_site["periode_start"],
            data_site["periode_end"],
            df_meteo_tre200d0,
        )
    except Exception as e:
        print(
            f"Erreur lors de la création du DataFrame de météo pour le calcul des degrés-jours. Erreur : {e}"
        )

    # générer dataframe df_list_idc
    df_list_idc = make_dataframe_df_list_idc(data_site, DJ_REF_ANNUELS)

    # df_agent_energetique
    (
        data_site["idc_agent_energetique_ef_mazout_somme_mj"],
        data_site["idc_agent_energetique_ef_gaz_naturel_somme_mj"],
        data_site["idc_agent_energetique_ef_bois_buches_dur_somme_mj"],
        data_site["idc_agent_energetique_ef_bois_buches_tendre_somme_mj"],
        data_site["idc_agent_energetique_ef_pellets_somme_mj"],
        data_site["idc_agent_energetique_ef_plaquettes_somme_mj"],
        data_site["idc_agent_energetique_ef_cad_reparti_somme_mj"],
        data_site["idc_agent_energetique_ef_cad_tarife_somme_mj"],
        data_site["idc_agent_energetique_ef_electricite_pac_avant_somme_mj"],
        data_site["idc_agent_energetique_ef_electricite_pac_apres_somme_mj"],
        data_site["idc_agent_energetique_ef_electricite_directe_somme_mj"],
        data_site["idc_agent_energetique_ef_autre_somme_mj"]
    ) = fonction_conversion_energie_idc(
        data_site["idc_agent_energetique_ef_cad_reparti_kwh"],
        data_site["idc_agent_energetique_ef_cad_tarife_kwh"],
        data_site["idc_agent_energetique_ef_electricite_pac_avant_kwh"],
        data_site["idc_agent_energetique_ef_electricite_pac_apres_kwh"],
        data_site["idc_agent_energetique_ef_electricite_directe_kwh"],
        data_site["idc_agent_energetique_ef_gaz_naturel_m3"],
        data_site["idc_agent_energetique_ef_gaz_naturel_kwh"],
        data_site["idc_agent_energetique_ef_mazout_litres"],
        data_site["idc_agent_energetique_ef_mazout_kg"],
        data_site["idc_agent_energetique_ef_mazout_kwh"],
        data_site["idc_agent_energetique_ef_bois_buches_dur_stere"],
        data_site["idc_agent_energetique_ef_bois_buches_tendre_stere"],
        data_site["idc_agent_energetique_ef_bois_buches_tendre_kwh"],
        data_site["idc_agent_energetique_ef_pellets_m3"],
        data_site["idc_agent_energetique_ef_pellets_kg"],
        data_site["idc_agent_energetique_ef_pellets_kwh"],
        data_site["idc_agent_energetique_ef_plaquettes_m3"],
        data_site["idc_agent_energetique_ef_plaquettes_kwh"],
        data_site["idc_agent_energetique_ef_autre_kwh"],
        data_site["idc_ecs_agent_energetique_ef_cad_reparti_kwh"],
        data_site["idc_ecs_agent_energetique_ef_cad_tarife_kwh"],
        data_site["idc_ecs_agent_energetique_ef_electricite_pac_avant_kwh"],
        data_site["idc_ecs_agent_energetique_ef_electricite_pac_apres_kwh"],
        data_site["idc_ecs_agent_energetique_ef_electricite_directe_kwh"],
        data_site["idc_ecs_agent_energetique_ef_gaz_naturel_m3"],
        data_site["idc_ecs_agent_energetique_ef_gaz_naturel_kwh"],
        data_site["idc_ecs_agent_energetique_ef_mazout_litres"],
        data_site["idc_ecs_agent_energetique_ef_mazout_kg"],
        data_site["idc_ecs_agent_energetique_ef_mazout_kwh"],
        data_site["idc_ecs_agent_energetique_ef_bois_buches_dur_stere"],
        data_site["idc_ecs_agent_energetique_ef_bois_buches_tendre_stere"],
        data_site["idc_ecs_agent_energetique_ef_bois_buches_tendre_kwh"],
        data_site["idc_ecs_agent_energetique_ef_pellets_m3"],
        data_site["idc_ecs_agent_energetique_ef_pellets_kg"],
        data_site["idc_ecs_agent_energetique_ef_pellets_kwh"],
        data_site["idc_ecs_agent_energetique_ef_plaquettes_m3"],
        data_site["idc_ecs_agent_energetique_ef_plaquettes_kwh"],
        data_site["idc_ecs_agent_energetique_ef_autre_kwh"],
        IDC_CONVERSION_CAD_REPARTI_MJ_KWH,
        IDC_CONVERSION_CAD_TARIFE_MJ_KWH,
        IDC_CONVERSION_ELECTRICITE_PAC_AVANT_MJ_KWH,
        IDC_CONVERSION_ELECTRICITE_PAC_APRES_MJ_KWH,
        IDC_CONVERSION_ELECTRICITE_DIRECTE_MJ_KWH,
        IDC_CONVERSION_GAZ_NATUREL_MJ_M3,
        IDC_CONVERSION_GAZ_NATUREL_MJ_KWH,
        IDC_CONVERSION_MAZOUT_MJ_LITRES,
        IDC_CONVERSION_MAZOUT_MJ_KG,
        IDC_CONVERSION_MAZOUT_MJ_KWH,
        IDC_CONVERSION_BOIS_BUCHES_DUR_MJ_STERE,
        IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_STERE,
        IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_KWH,
        IDC_CONVERSION_PELLETS_MJ_M3,
        IDC_CONVERSION_PELLETS_MJ_KG,
        IDC_CONVERSION_PELLETS_MJ_KWH,
        IDC_CONVERSION_PLAQUETTES_MJ_M3,
        IDC_CONVERSION_PLAQUETTES_MJ_KWH,
        IDC_CONVERSION_AUTRE_MJ_KWH,
        IDC_FACTEUR_PONDERATION_CAD,
        IDC_FACTEUR_PONDERATION_GAZ_NATUREL,
        IDC_FACTEUR_PONDERATION_BOIS_BUCHES_DUR,
        IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE,
        IDC_FACTEUR_PONDERATION_PELLETS,
        IDC_FACTEUR_PONDERATION_PLAQUETTES,
        IDC_FACTEUR_PONDERATION_MAZOUT,
        IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_AVANT,
        IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_APRES,
        IDC_FACTEUR_PONDERATION_ELECTRICITE_DIRECTE,
        IDC_FACTEUR_PONDERATION_AUTRE,
        )

    (df_agent_energetique_idc_sum,
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
    ) = make_dataframe_df_agent_energetique_idc(
        data_site,
        IDC_CONVERSION_CAD_REPARTI_MJ_KWH,
        IDC_CONVERSION_CAD_TARIFE_MJ_KWH,
        IDC_CONVERSION_ELECTRICITE_PAC_AVANT_MJ_KWH,
        IDC_CONVERSION_ELECTRICITE_PAC_APRES_MJ_KWH,
        IDC_CONVERSION_ELECTRICITE_DIRECTE_MJ_KWH,
        IDC_CONVERSION_GAZ_NATUREL_MJ_M3,
        IDC_CONVERSION_GAZ_NATUREL_MJ_KWH,
        IDC_CONVERSION_MAZOUT_MJ_LITRES,
        IDC_CONVERSION_MAZOUT_MJ_KG,
        IDC_CONVERSION_MAZOUT_MJ_KWH,
        IDC_CONVERSION_BOIS_BUCHES_DUR_MJ_STERE,
        IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_STERE,
        IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_KWH,
        IDC_CONVERSION_PELLETS_MJ_M3,
        IDC_CONVERSION_PELLETS_MJ_KG,
        IDC_CONVERSION_PELLETS_MJ_KWH,
        IDC_CONVERSION_PLAQUETTES_MJ_M3,
        IDC_CONVERSION_PLAQUETTES_MJ_KWH,
        IDC_CONVERSION_AUTRE_MJ_KWH,
        IDC_FACTEUR_PONDERATION_MAZOUT,
        IDC_FACTEUR_PONDERATION_GAZ_NATUREL,
        IDC_FACTEUR_PONDERATION_BOIS_BUCHES_DUR,
        IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE,
        IDC_FACTEUR_PONDERATION_PELLETS,
        IDC_FACTEUR_PONDERATION_PLAQUETTES,
        IDC_FACTEUR_PONDERATION_CAD,
        IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_AVANT,
        IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_APRES,
        IDC_FACTEUR_PONDERATION_ELECTRICITE_DIRECTE,
        IDC_FACTEUR_PONDERATION_AUTRE)

    return (
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

    )
