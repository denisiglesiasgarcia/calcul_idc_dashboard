# sections/note_calcul.py

# import pandas as pd
# import streamlit as st

from sections.helpers.note_calcul.create_dataframe_periode_list import (
    make_dataframe_df_periode_list,
)

from sections.helpers.note_calcul.create_dataframe_list import make_dataframe_df_list

from sections.helpers.note_calcul.create_dataframe_agent_energetique import (
    make_dataframe_df_agent_energetique,
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
    fonction_idc_eww_theorique_comptage_ecs_inclus_mj_m2,
    fonction_idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj,
    fonction_idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj,
    fonction_idc_eww_part_energie_finale_ecs_comptage_ecs_inclus_mj_m2,
    fonction_idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2,
    fonction_idc_bh_energie_finale_chauffage_comptage_ecs_inclus_mj,
    fonction_idc_bh_energie_finale_chauffage_comptage_ecs_non_inclus_mj,
    fonction_idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_inclus_mj_m2,
    fonction_idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_non_inclus_mj_m2,
    fonction_idc_resultat_comptage_ecs_inclus_mj_m2,
    fonction_idc_resultat_comptage_ecs_non_inclus_mj_m2,
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

from sections.helpers.note_calcul.latex import (
    make_latex_formula_facteur_ponderation_moyen,
)


def fonction_note_calcul_idc(data_site, df_meteo_tre200d0):
    """
    déjà dans data_site:
    - data_site["periode_start"]
    - data_site["periode_end"]
    - data_site["periode_nb_jours"]
    - data_site["idc_sre_m2"]
 

    Calculs réalisés ici:



    éléments créés:
    - df_periode_list (dataframe des periodes considérées)


    """

    # df_periode_list
    df_periode_list = make_dataframe_df_periode_list(
        data_site["periode_start"], data_site["periode_end"]
    )

    # météo
    data_site["dj_periode"] = calcul_dj_periode(
        df_meteo_tre200d0,
        data_site["periode_start"],
        data_site["periode_end"],
    )

    # IDC
    try:
        # cas comptage ECS inclus
        if data_site["comptage_ecs_inclus"]:
            # ECS
            # C119
            data_site["idc_eww_theorique_comptage_ecs_inclus_mj_m2"] = fonction_idc_eww_theorique_comptage_ecs_inclus_mj_m2(
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
                data_site["idc_eww_theorique_comptage_ecs_inclus_mj_m2"],
                data_site["idc_sre_m2"],
                data_site["periode_nb_jours"],
                )

            data_site["idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj"] = 0

            # C119
            data_site["idc_eww_part_energie_finale_ecs_comptage_ecs_inclus_mj_m2"] = fonction_idc_eww_part_energie_finale_ecs_comptage_ecs_inclus_mj_m2(
                data_site["idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj"],
                data_site["idc_sre_m2"],
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
                data_site["idc_eww_part_energie_finale_ecs_comptage_ecs_inclus_mj_m2"],
                data_site["idc_sre_m2"],
                DJ_REF_ANNUELS,
                data_site["dj_periode"]
            )
            # Total
            # C124
            data_site["idc_resultat_comptage_ecs_inclus_mj_m2"] = fonction_idc_resultat_comptage_ecs_inclus_mj_m2(
                data_site["idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_inclus_mj_m2"],
                data_site["idc_eww_part_energie_finale_ecs_comptage_ecs_inclus_mj_m2"],
            )

        # cas comptage ECS pas inclus
        else:
            # ECS
            # C118
            data_site["idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj"] = 0
            
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
            data_site["idc_eww_theorique_comptage_ecs_inclus_mj_m2"] = 0
            
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


    except Exception as e:
        print("error", e)
        # ECS
        data_site["idc_eww_pondere_mj_m2"] = 0
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

    

    # générer dataframe df_list
    df_list = make_dataframe_df_list(data_site, DJ_REF_ANNUELS)

    # # df_agent_energetique
    # df_agent_energetique = make_dataframe_df_agent_energetique(
    #     data_site,
    #     FACTEUR_PONDERATION_MAZOUT,
    #     FACTEUR_PONDERATION_GAZ_NATUREL,
    #     FACTEUR_PONDERATION_BOIS_BUCHES_DUR,
    #     FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE,
    #     FACTEUR_PONDERATION_PELLETS,
    #     FACTEUR_PONDERATION_PLAQUETTES,
    #     FACTEUR_PONDERATION_CAD,
    #     FACTEUR_PONDERATION_ELECTRICITE_PAC,
    #     FACTEUR_PONDERATION_ELECTRICITE_DIRECTE,
    #     FACTEUR_PONDERATION_AUTRE,
    # )

    # # df_meteo_note_calcul
    # df_meteo_note_calcul = make_dataframe_df_meteo_note_calcul(
    #     data_site["periode_start"],
    #     data_site["periode_end"],
    #     df_meteo_tre200d0,
    # )

    # # df_results
    # df_results = make_dataframe_df_results(
    #     data_site["ef_avant_corr_kwh_m2"],
    #     data_site["ef_objectif_pondere_kwh_m2"],
    #     data_site["delta_ef_realisee_kwh_m2"],
    #     data_site["delta_ef_visee_kwh_m2"],
    #     data_site[
    #         "energie_finale_apres_travaux_climatiquement_corrigee_renovee_pondere_kwh_m2"
    #     ],
    # )

    # # latex text
    # formula_facteur_ponderation_moyen_texte = r"facteur\_ponderation\_moyen = \frac{{(agent\_energetique\_mazout\_somme\_mj \times FACTEUR\_PONDERATION\_MAZOUT + \
    #             agent\_energetique\_gaz\_naturel\_somme\_mj \times FACTEUR\_PONDERATION\_GAZ\_NATUREL + \
    #             agent\_energetique\_bois\_buches\_dur\_somme\_mj \times FACTEUR\_PONDERATION\_BOIS\_BUCHES\_DUR + \
    #             agent\_energetique\_bois\_buches\_tendre\_somme\_mj \times FACTEUR\_PONDERATION\_BOIS\_BUCHES\_TENDRE + \
    #             agent\_energetique\_pellets\_somme\_mj \times FACTEUR\_PONDERATION\_PELLETS + \
    #             agent\_energetique\_plaquettes\_somme\_mj \times FACTEUR\_PONDERATION\_PLAQUETTES + \
    #             agent\_energetique\_cad\_somme\_mj \times FACTEUR\_PONDERATION\_CAD + \
    #             agent\_energetique\_electricite\_pac\_somme\_mj \times FACTEUR\_PONDERATION\_ELECTRICITE\_PAC + \
    #             agent\_energetique\_electricite\_directe\_somme\_mj \times FACTEUR\_PONDERATION\_ELECTRICITE\_DIRECTE + \
    #             agent\_energetique\_autre\_somme\_mj \times FACTEUR\_PONDERATION\_AUTRE)}}{{(agent\_energetique\_somme\_kwh \times 3.6)}}"

    # # latex formula
    # formula_facteur_ponderation_moyen = make_latex_formula_facteur_ponderation_moyen(
    #     data_site["agent_energetique_ef_mazout_somme_mj"],
    #     data_site["agent_energetique_ef_gaz_naturel_somme_mj"],
    #     data_site["agent_energetique_ef_bois_buches_dur_somme_mj"],
    #     data_site["agent_energetique_ef_bois_buches_tendre_somme_mj"],
    #     data_site["agent_energetique_ef_pellets_somme_mj"],
    #     data_site["agent_energetique_ef_plaquettes_somme_mj"],
    #     data_site["agent_energetique_ef_cad_somme_mj"],
    #     data_site["agent_energetique_ef_electricite_pac_somme_mj"],
    #     data_site["agent_energetique_ef_electricite_directe_somme_mj"],
    #     data_site["agent_energetique_ef_autre_somme_mj"],
    #     data_site["agent_energetique_ef_somme_kwh"],
    #     data_site["facteur_ponderation_moyen"],
    #     FACTEUR_PONDERATION_MAZOUT,
    #     FACTEUR_PONDERATION_GAZ_NATUREL,
    #     FACTEUR_PONDERATION_BOIS_BUCHES_DUR,
    #     FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE,
    #     FACTEUR_PONDERATION_PELLETS,
    #     FACTEUR_PONDERATION_PLAQUETTES,
    #     FACTEUR_PONDERATION_CAD,
    #     FACTEUR_PONDERATION_ELECTRICITE_PAC,
    #     FACTEUR_PONDERATION_ELECTRICITE_DIRECTE,
    #     FACTEUR_PONDERATION_AUTRE,
    # )

    return (
        df_periode_list,
        df_list,
        df_agent_energetique,
        df_meteo_note_calcul,
        df_results,
        formula_facteur_ponderation_moyen_texte,
        formula_facteur_ponderation_moyen,
    )
