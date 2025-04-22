# sections/helpers/note_calcul/calculs_idc.py


# C119 → Eww part d'énergie finale pour l'ECS
def fonction_idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2(
    sre_pourcentage_habitat_collectif,
    sre_pourcentage_habitat_individuel,
    sre_pourcentage_administration,
    sre_pourcentage_ecoles,
    sre_pourcentage_commerce,
    sre_pourcentage_restauration,
    sre_pourcentage_lieux_de_rassemblement,
    sre_pourcentage_hopitaux,
    sre_pourcentage_industrie,
    sre_pourcentage_depots,
    sre_pourcentage_installations_sportives,
    sre_pourcentage_piscines_couvertes,
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
):
    """ 
    Pondération des besoins d'énergie pour l'ECS théoriques
    Eww = (Qww/(0.9*0.65) pour le calcul du Bww sans comptage séparé.
    """
    try:
        if (
            sre_pourcentage_habitat_collectif >= 0
            and sre_pourcentage_habitat_individuel >= 0
            and sre_pourcentage_administration >= 0
            and sre_pourcentage_ecoles >= 0
            and sre_pourcentage_commerce >= 0
            and sre_pourcentage_restauration >= 0
            and sre_pourcentage_lieux_de_rassemblement >= 0
            and sre_pourcentage_hopitaux >= 0
            and sre_pourcentage_industrie >= 0
            and sre_pourcentage_depots >= 0
            and sre_pourcentage_installations_sportives >= 0
            and sre_pourcentage_piscines_couvertes >= 0
        ):
            idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2 = (
                sre_pourcentage_habitat_collectif * IDC_EWW_HABITAT_COLLECTIF_MJ_M2 +
                sre_pourcentage_habitat_individuel * IDC_EWW_HABITAT_INDIVIDUEL_MJ_M2 +
                sre_pourcentage_administration * IDC_EWW_ADMINISTRATION_MJ_M2 +
                sre_pourcentage_ecoles * IDC_EWW_ECOLES_MJ_M2 +
                sre_pourcentage_commerce * IDC_EWW_COMMERCE_MJ_M2 +
                sre_pourcentage_restauration * IDC_EWW_RESTAURATION_MJ_M2 +
                sre_pourcentage_lieux_de_rassemblement * IDC_EWW_LIEUX_DE_RASSEMBLEMENT_MJ_M2 +
                sre_pourcentage_hopitaux * IDC_EWW_HOPITAUX_MJ_M2 +
                sre_pourcentage_industrie * IDC_EWW_INDUSTRIE_MJ_M2 +
                sre_pourcentage_depots * IDC_EWW_DEPOTS_MJ_M2 +
                sre_pourcentage_installations_sportives * IDC_EWW_INSTALLATIONS_SPORTIVES_MJ_M2 +
                sre_pourcentage_piscines_couvertes * IDC_EWW_PISCINES_COUVERTES_MJ_M2
            )/(
                sre_pourcentage_habitat_collectif +
                sre_pourcentage_habitat_individuel +
                sre_pourcentage_administration +
                sre_pourcentage_ecoles +
                sre_pourcentage_commerce +
                sre_pourcentage_restauration +
                sre_pourcentage_lieux_de_rassemblement +
                sre_pourcentage_hopitaux +
                sre_pourcentage_industrie +
                sre_pourcentage_depots +
                sre_pourcentage_installations_sportives +
                sre_pourcentage_piscines_couvertes
            )
        else:
            idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2 = 0
    except Exception as e:
        print(e)
        idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2 = 0
    return idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2

# C118 Bww → Energie finale pour l'ECS
def fonction_idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj(
    idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2,
    idc_sre_m2,
    periode_nb_jours,
    ):
    """
    Si pas de comptage indépendant c'est ((Qww/(0.9*0.65)) * Ae) * (nb_jours/365)
    Eww = (Qww/(0.9*0.65) donc Bww = Eww * Ae * (nb_jours/365).
    nb_jours/365 pour tenir compte des cas ou la période ne fait pas 365 jours
    """
    try:
        if idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2 > 0 and idc_sre_m2 > 0:
            idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj = (
                idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2 * idc_sre_m2 * (periode_nb_jours / 365)
            )
        else:
            idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj = 0
    except Exception as e:
        print(e)
        idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj = 0
    return idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj


# C120 → Bh énergie finale pour le chauffage
def fonction_idc_bh_energie_finale_chauffage_comptage_ecs_inclus_mj(
    idc_agent_energetique_ef_cad_reparti_kwh,
    idc_agent_energetique_ef_cad_tarife_kwh,
    idc_agent_energetique_ef_electricite_pac_avant_kwh,
    idc_agent_energetique_ef_electricite_pac_apres_kwh,
    idc_agent_energetique_ef_electricite_directe_kwh,
    idc_agent_energetique_ef_gaz_naturel_m3,
    idc_agent_energetique_ef_gaz_naturel_kwh,
    idc_agent_energetique_ef_mazout_litres,
    idc_agent_energetique_ef_mazout_kg,
    idc_agent_energetique_ef_mazout_kwh,
    idc_agent_energetique_ef_bois_buches_dur_stere,
    idc_agent_energetique_ef_bois_buches_tendre_stere,
    idc_agent_energetique_ef_bois_buches_tendre_kwh,
    idc_agent_energetique_ef_pellets_m3,
    idc_agent_energetique_ef_pellets_kg,
    idc_agent_energetique_ef_pellets_kwh,
    idc_agent_energetique_ef_plaquettes_m3,
    idc_agent_energetique_ef_plaquettes_kwh,
    idc_agent_energetique_ef_autre_kwh,
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
    idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj
    ):
    """
    Bh énergie finale pour le chauffage en MJ
    il s'agit de l'énergie finale totale - l'énergie finale pour l'ECS (cas comptage ECS inclus)
    """
    try:
        if (
            idc_agent_energetique_ef_cad_reparti_kwh >= 0
            and idc_agent_energetique_ef_cad_tarife_kwh >= 0
            and idc_agent_energetique_ef_electricite_pac_avant_kwh >= 0
            and idc_agent_energetique_ef_electricite_pac_apres_kwh >= 0
            and idc_agent_energetique_ef_electricite_directe_kwh >= 0
            and idc_agent_energetique_ef_gaz_naturel_m3 >= 0
            and idc_agent_energetique_ef_gaz_naturel_kwh >= 0
            and idc_agent_energetique_ef_mazout_litres >= 0
            and idc_agent_energetique_ef_mazout_kg >= 0
            and idc_agent_energetique_ef_mazout_kwh >= 0
            and idc_agent_energetique_ef_bois_buches_dur_stere >= 0
            and idc_agent_energetique_ef_bois_buches_tendre_stere >= 0
            and idc_agent_energetique_ef_bois_buches_tendre_kwh >= 0
            and idc_agent_energetique_ef_pellets_m3 >= 0
            and idc_agent_energetique_ef_pellets_kg >= 0
            and idc_agent_energetique_ef_pellets_kwh >= 0
            and idc_agent_energetique_ef_plaquettes_m3 >= 0
            and idc_agent_energetique_ef_plaquettes_kwh >= 0
            and idc_agent_energetique_ef_autre_kwh >= 0
        ):
            idc_bh_energie_finale_chauffage_comptage_ecs_inclus_mj = ((
                idc_agent_energetique_ef_cad_reparti_kwh * IDC_CONVERSION_CAD_REPARTI_MJ_KWH * IDC_FACTEUR_PONDERATION_CAD +
                idc_agent_energetique_ef_cad_tarife_kwh * IDC_CONVERSION_CAD_TARIFE_MJ_KWH * IDC_FACTEUR_PONDERATION_CAD +
                idc_agent_energetique_ef_electricite_pac_avant_kwh * IDC_CONVERSION_ELECTRICITE_PAC_AVANT_MJ_KWH * IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_AVANT +
                idc_agent_energetique_ef_electricite_pac_apres_kwh * IDC_CONVERSION_ELECTRICITE_PAC_APRES_MJ_KWH * IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_APRES +
                idc_agent_energetique_ef_electricite_directe_kwh * IDC_CONVERSION_ELECTRICITE_DIRECTE_MJ_KWH * IDC_FACTEUR_PONDERATION_ELECTRICITE_DIRECTE +
                idc_agent_energetique_ef_gaz_naturel_m3 * IDC_CONVERSION_GAZ_NATUREL_MJ_M3 * IDC_FACTEUR_PONDERATION_GAZ_NATUREL +
                idc_agent_energetique_ef_gaz_naturel_kwh * IDC_CONVERSION_GAZ_NATUREL_MJ_KWH * IDC_FACTEUR_PONDERATION_GAZ_NATUREL +
                idc_agent_energetique_ef_mazout_litres * IDC_CONVERSION_MAZOUT_MJ_LITRES * IDC_FACTEUR_PONDERATION_MAZOUT +
                idc_agent_energetique_ef_mazout_kg * IDC_CONVERSION_MAZOUT_MJ_KG * IDC_FACTEUR_PONDERATION_MAZOUT +
                idc_agent_energetique_ef_mazout_kwh * IDC_CONVERSION_MAZOUT_MJ_KWH * IDC_FACTEUR_PONDERATION_MAZOUT +
                idc_agent_energetique_ef_bois_buches_dur_stere * IDC_CONVERSION_BOIS_BUCHES_DUR_MJ_STERE * IDC_FACTEUR_PONDERATION_BOIS_BUCHES_DUR +
                idc_agent_energetique_ef_bois_buches_tendre_stere * IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_STERE * IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE +
                idc_agent_energetique_ef_bois_buches_tendre_kwh * IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_KWH * IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE +
                idc_agent_energetique_ef_pellets_m3 * IDC_CONVERSION_PELLETS_MJ_M3 * IDC_FACTEUR_PONDERATION_PELLETS +
                idc_agent_energetique_ef_pellets_kg * IDC_CONVERSION_PELLETS_MJ_KG * IDC_FACTEUR_PONDERATION_PELLETS +
                idc_agent_energetique_ef_pellets_kwh * IDC_CONVERSION_PELLETS_MJ_KWH * IDC_FACTEUR_PONDERATION_PELLETS +
                idc_agent_energetique_ef_plaquettes_m3 * IDC_CONVERSION_PLAQUETTES_MJ_M3 * IDC_FACTEUR_PONDERATION_PLAQUETTES +
                idc_agent_energetique_ef_plaquettes_kwh * IDC_CONVERSION_PLAQUETTES_MJ_KWH * IDC_FACTEUR_PONDERATION_PLAQUETTES +
                idc_agent_energetique_ef_autre_kwh * IDC_CONVERSION_AUTRE_MJ_KWH * IDC_FACTEUR_PONDERATION_AUTRE) - idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj)
        else:
            idc_bh_energie_finale_chauffage_comptage_ecs_inclus_mj = 0
    except Exception as e:
        print(e)
        idc_bh_energie_finale_chauffage_comptage_ecs_inclus_mj = 0
    return idc_bh_energie_finale_chauffage_comptage_ecs_inclus_mj


# C123 → Eh Part d'énergie finale pour le chauffage avec correction climatique
def fonction_idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_inclus_mj_m2(
    idc_bh_energie_finale_chauffage_comptage_ecs_inclus_mj,
    idc_sre_m2,
    DJ_REF_ANNUELS,
    dj_periode
):
    try:
        if (idc_sre_m2 > 0 and DJ_REF_ANNUELS > 0 and dj_periode > 0 and isinstance(idc_bh_energie_finale_chauffage_comptage_ecs_inclus_mj, (int, float))):
            idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_inclus_mj_m2 = (
                (idc_bh_energie_finale_chauffage_comptage_ecs_inclus_mj / idc_sre_m2)*(DJ_REF_ANNUELS/dj_periode))
        else:
            idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_inclus_mj_m2 = 0
    except Exception as e:
        print(e)
        idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_inclus_mj_m2 = 0
    return idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_inclus_mj_m2


# C124 → IDC = Eh + Eww
def fonction_idc_resultat_comptage_ecs_inclus_mj_m2(
    idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_inclus_mj_m2,
    idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2
):
    """
    IDC = Eh + Eww
    """
    try:
        if (isinstance(idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_inclus_mj_m2, (int, float))) and isinstance(idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2, (int, float)):
            idc_resultat_comptage_ecs_inclus_mj_m2 = (
                idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_inclus_mj_m2 +
                idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2
            )
        else:
            idc_resultat_comptage_ecs_inclus_mj_m2 = 0
    except Exception as e:
        print(e)
        idc_resultat_comptage_ecs_inclus_mj_m2 = 0
    return idc_resultat_comptage_ecs_inclus_mj_m2


#####################################################################################################
##################################### ECS pas inclus ################################################

# C118
def fonction_idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj(
    idc_ecs_agent_energetique_ef_cad_reparti_kwh,
    idc_ecs_agent_energetique_ef_cad_tarife_kwh,
    idc_ecs_agent_energetique_ef_electricite_pac_avant_kwh,
    idc_ecs_agent_energetique_ef_electricite_pac_apres_kwh,
    idc_ecs_agent_energetique_ef_electricite_directe_kwh,
    idc_ecs_agent_energetique_ef_gaz_naturel_m3,
    idc_ecs_agent_energetique_ef_gaz_naturel_kwh,
    idc_ecs_agent_energetique_ef_mazout_litres,
    idc_ecs_agent_energetique_ef_mazout_kg,
    idc_ecs_agent_energetique_ef_mazout_kwh,
    idc_ecs_agent_energetique_ef_bois_buches_dur_stere,
    idc_ecs_agent_energetique_ef_bois_buches_tendre_stere,
    idc_ecs_agent_energetique_ef_bois_buches_tendre_kwh,
    idc_ecs_agent_energetique_ef_pellets_m3,
    idc_ecs_agent_energetique_ef_pellets_kg,
    idc_ecs_agent_energetique_ef_pellets_kwh,
    idc_ecs_agent_energetique_ef_plaquettes_m3,
    idc_ecs_agent_energetique_ef_plaquettes_kwh,
    idc_ecs_agent_energetique_ef_autre_kwh,
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
    ):
    """
    Somme des agents énergétiques pour l'ECS en MJ
    """
    try:
        if (
            idc_ecs_agent_energetique_ef_cad_reparti_kwh >= 0
            and idc_ecs_agent_energetique_ef_cad_tarife_kwh >= 0
            and idc_ecs_agent_energetique_ef_electricite_pac_avant_kwh >= 0
            and idc_ecs_agent_energetique_ef_electricite_pac_apres_kwh >= 0
            and idc_ecs_agent_energetique_ef_electricite_directe_kwh >= 0
            and idc_ecs_agent_energetique_ef_gaz_naturel_m3 >= 0
            and idc_ecs_agent_energetique_ef_gaz_naturel_kwh >= 0
            and idc_ecs_agent_energetique_ef_mazout_litres >= 0
            and idc_ecs_agent_energetique_ef_mazout_kg >= 0
            and idc_ecs_agent_energetique_ef_mazout_kwh >= 0
            and idc_ecs_agent_energetique_ef_bois_buches_dur_stere >= 0
            and idc_ecs_agent_energetique_ef_bois_buches_tendre_stere >= 0
            and idc_ecs_agent_energetique_ef_bois_buches_tendre_kwh >= 0
            and idc_ecs_agent_energetique_ef_pellets_m3 >= 0
            and idc_ecs_agent_energetique_ef_pellets_kg >= 0
            and idc_ecs_agent_energetique_ef_pellets_kwh >= 0
            and idc_ecs_agent_energetique_ef_plaquettes_m3 >= 0
            and idc_ecs_agent_energetique_ef_plaquettes_kwh >= 0
            and idc_ecs_agent_energetique_ef_autre_kwh >= 0
        ):
            idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj = (
                idc_ecs_agent_energetique_ef_cad_reparti_kwh * IDC_CONVERSION_CAD_REPARTI_MJ_KWH * IDC_FACTEUR_PONDERATION_CAD +
                idc_ecs_agent_energetique_ef_cad_tarife_kwh * IDC_CONVERSION_CAD_TARIFE_MJ_KWH * IDC_FACTEUR_PONDERATION_CAD +
                idc_ecs_agent_energetique_ef_electricite_pac_avant_kwh * IDC_CONVERSION_ELECTRICITE_PAC_AVANT_MJ_KWH * IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_AVANT +
                idc_ecs_agent_energetique_ef_electricite_pac_apres_kwh * IDC_CONVERSION_ELECTRICITE_PAC_APRES_MJ_KWH * IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_APRES +
                idc_ecs_agent_energetique_ef_electricite_directe_kwh * IDC_CONVERSION_ELECTRICITE_DIRECTE_MJ_KWH * IDC_FACTEUR_PONDERATION_ELECTRICITE_DIRECTE +
                idc_ecs_agent_energetique_ef_gaz_naturel_m3 * IDC_CONVERSION_GAZ_NATUREL_MJ_M3 * IDC_FACTEUR_PONDERATION_GAZ_NATUREL +
                idc_ecs_agent_energetique_ef_gaz_naturel_kwh * IDC_CONVERSION_GAZ_NATUREL_MJ_KWH * IDC_FACTEUR_PONDERATION_GAZ_NATUREL +
                idc_ecs_agent_energetique_ef_mazout_litres * IDC_CONVERSION_MAZOUT_MJ_LITRES * IDC_FACTEUR_PONDERATION_MAZOUT +
                idc_ecs_agent_energetique_ef_mazout_kg * IDC_CONVERSION_MAZOUT_MJ_KG * IDC_FACTEUR_PONDERATION_MAZOUT +
                idc_ecs_agent_energetique_ef_mazout_kwh * IDC_CONVERSION_MAZOUT_MJ_KWH * IDC_FACTEUR_PONDERATION_MAZOUT +
                idc_ecs_agent_energetique_ef_bois_buches_dur_stere * IDC_CONVERSION_BOIS_BUCHES_DUR_MJ_STERE * IDC_FACTEUR_PONDERATION_BOIS_BUCHES_DUR +
                idc_ecs_agent_energetique_ef_bois_buches_tendre_stere * IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_STERE * IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE +
                idc_ecs_agent_energetique_ef_bois_buches_tendre_kwh * IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_KWH * IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE +
                idc_ecs_agent_energetique_ef_pellets_m3 * IDC_CONVERSION_PELLETS_MJ_M3 * IDC_FACTEUR_PONDERATION_PELLETS +
                idc_ecs_agent_energetique_ef_pellets_kg * IDC_CONVERSION_PELLETS_MJ_KG * IDC_FACTEUR_PONDERATION_PELLETS +
                idc_ecs_agent_energetique_ef_pellets_kwh * IDC_CONVERSION_PELLETS_MJ_KWH * IDC_FACTEUR_PONDERATION_PELLETS +
                idc_ecs_agent_energetique_ef_plaquettes_m3 * IDC_CONVERSION_PLAQUETTES_MJ_M3 * IDC_FACTEUR_PONDERATION_PLAQUETTES +
                idc_ecs_agent_energetique_ef_plaquettes_kwh * IDC_CONVERSION_PLAQUETTES_MJ_KWH * IDC_FACTEUR_PONDERATION_PLAQUETTES +
                idc_ecs_agent_energetique_ef_autre_kwh * IDC_CONVERSION_AUTRE_MJ_KWH * IDC_FACTEUR_PONDERATION_AUTRE
            )
        else:
            idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj = 0
    except Exception as e:
        print(e)
        idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj = 0
    return idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj

# C119
def fonction_idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2(idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj, idc_sre_m2):
    """
    Eww part d'énergie finale pour l'ECS dans le cas de comptage séparé de l'ECS. Possible d'aller au dela des valeurs SIA 380/1.
    """
    try:
        if idc_sre_m2 > 0:
            idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2 = (
                idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj / idc_sre_m2
            )
        else:
            idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2 = 0
    except Exception as e:
        print(e)
        idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2 = 0
    return idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2

# C120
def fonction_idc_bh_energie_finale_chauffage_comptage_ecs_non_inclus_mj(
    idc_agent_energetique_ef_cad_reparti_kwh,
    idc_agent_energetique_ef_cad_tarife_kwh,
    idc_agent_energetique_ef_electricite_pac_avant_kwh,
    idc_agent_energetique_ef_electricite_pac_apres_kwh,
    idc_agent_energetique_ef_electricite_directe_kwh,
    idc_agent_energetique_ef_gaz_naturel_m3,
    idc_agent_energetique_ef_gaz_naturel_kwh,
    idc_agent_energetique_ef_mazout_litres,
    idc_agent_energetique_ef_mazout_kg,
    idc_agent_energetique_ef_mazout_kwh,
    idc_agent_energetique_ef_bois_buches_dur_stere,
    idc_agent_energetique_ef_bois_buches_tendre_stere,
    idc_agent_energetique_ef_bois_buches_tendre_kwh,
    idc_agent_energetique_ef_pellets_m3,
    idc_agent_energetique_ef_pellets_kg,
    idc_agent_energetique_ef_pellets_kwh,
    idc_agent_energetique_ef_plaquettes_m3,
    idc_agent_energetique_ef_plaquettes_kwh,
    idc_agent_energetique_ef_autre_kwh,
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
    idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj
    ):
    """
    Bww énergie finale pour le chauffage en MJ
    il s'agit de l'énergie finale totale - l'énergie finale pour l'ECS (cas de comptage ECS non inclus)
    """
    try:
        if (
            idc_agent_energetique_ef_cad_reparti_kwh >= 0
            and idc_agent_energetique_ef_cad_tarife_kwh >= 0
            and idc_agent_energetique_ef_electricite_pac_avant_kwh >= 0
            and idc_agent_energetique_ef_electricite_pac_apres_kwh >= 0
            and idc_agent_energetique_ef_electricite_directe_kwh >= 0
            and idc_agent_energetique_ef_gaz_naturel_m3 >= 0
            and idc_agent_energetique_ef_gaz_naturel_kwh >= 0
            and idc_agent_energetique_ef_mazout_litres >= 0
            and idc_agent_energetique_ef_mazout_kg >= 0
            and idc_agent_energetique_ef_mazout_kwh >= 0
            and idc_agent_energetique_ef_bois_buches_dur_stere >= 0
            and idc_agent_energetique_ef_bois_buches_tendre_stere >= 0
            and idc_agent_energetique_ef_bois_buches_tendre_kwh >= 0
            and idc_agent_energetique_ef_pellets_m3 >= 0
            and idc_agent_energetique_ef_pellets_kg >= 0
            and idc_agent_energetique_ef_pellets_kwh >= 0
            and idc_agent_energetique_ef_plaquettes_m3 >= 0
            and idc_agent_energetique_ef_plaquettes_kwh >= 0
            and idc_agent_energetique_ef_autre_kwh >= 0
            and idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj >= 0
        ):
            idc_bh_energie_finale_chauffage_comptage_ecs_non_inclus_mj = (
                idc_agent_energetique_ef_cad_reparti_kwh * IDC_CONVERSION_CAD_REPARTI_MJ_KWH * IDC_FACTEUR_PONDERATION_CAD +
                idc_agent_energetique_ef_cad_tarife_kwh * IDC_CONVERSION_CAD_TARIFE_MJ_KWH * IDC_FACTEUR_PONDERATION_CAD +
                idc_agent_energetique_ef_electricite_pac_avant_kwh * IDC_CONVERSION_ELECTRICITE_PAC_AVANT_MJ_KWH * IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_AVANT +
                idc_agent_energetique_ef_electricite_pac_apres_kwh * IDC_CONVERSION_ELECTRICITE_PAC_APRES_MJ_KWH * IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_APRES +
                idc_agent_energetique_ef_electricite_directe_kwh * IDC_CONVERSION_ELECTRICITE_DIRECTE_MJ_KWH * IDC_FACTEUR_PONDERATION_ELECTRICITE_DIRECTE +
                idc_agent_energetique_ef_gaz_naturel_m3 * IDC_CONVERSION_GAZ_NATUREL_MJ_M3 * IDC_FACTEUR_PONDERATION_GAZ_NATUREL +
                idc_agent_energetique_ef_gaz_naturel_kwh * IDC_CONVERSION_GAZ_NATUREL_MJ_KWH * IDC_FACTEUR_PONDERATION_GAZ_NATUREL +
                idc_agent_energetique_ef_mazout_litres * IDC_CONVERSION_MAZOUT_MJ_LITRES * IDC_FACTEUR_PONDERATION_MAZOUT +
                idc_agent_energetique_ef_mazout_kg * IDC_CONVERSION_MAZOUT_MJ_KG * IDC_FACTEUR_PONDERATION_MAZOUT +
                idc_agent_energetique_ef_mazout_kwh * IDC_CONVERSION_MAZOUT_MJ_KWH * IDC_FACTEUR_PONDERATION_MAZOUT +
                idc_agent_energetique_ef_bois_buches_dur_stere * IDC_CONVERSION_BOIS_BUCHES_DUR_MJ_STERE * IDC_FACTEUR_PONDERATION_BOIS_BUCHES_DUR +
                idc_agent_energetique_ef_bois_buches_tendre_stere * IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_STERE * IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE +
                idc_agent_energetique_ef_bois_buches_tendre_kwh * IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_KWH * IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE +
                idc_agent_energetique_ef_pellets_m3 * IDC_CONVERSION_PELLETS_MJ_M3 * IDC_FACTEUR_PONDERATION_PELLETS +
                idc_agent_energetique_ef_pellets_kg * IDC_CONVERSION_PELLETS_MJ_KG * IDC_FACTEUR_PONDERATION_PELLETS +
                idc_agent_energetique_ef_pellets_kwh * IDC_CONVERSION_PELLETS_MJ_KWH * IDC_FACTEUR_PONDERATION_PELLETS +
                idc_agent_energetique_ef_plaquettes_m3 * IDC_CONVERSION_PLAQUETTES_MJ_M3 * IDC_FACTEUR_PONDERATION_PLAQUETTES +
                idc_agent_energetique_ef_plaquettes_kwh * IDC_CONVERSION_PLAQUETTES_MJ_KWH * IDC_FACTEUR_PONDERATION_PLAQUETTES +
                idc_agent_energetique_ef_autre_kwh * IDC_CONVERSION_AUTRE_MJ_KWH * IDC_FACTEUR_PONDERATION_AUTRE)
        else:
            idc_bh_energie_finale_chauffage_comptage_ecs_non_inclus_mj = 0.0
    except Exception as e:
        print(e)
        idc_bh_energie_finale_chauffage_comptage_ecs_non_inclus_mj = 0.0
    return idc_bh_energie_finale_chauffage_comptage_ecs_non_inclus_mj

# C123
def fonction_idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_non_inclus_mj_m2(
    idc_bh_energie_finale_chauffage_comptage_ecs_non_inclus_mj,
    idc_sre_m2,
    DJ_REF_ANNUELS,
    dj_periode
):
    try:
        if (idc_sre_m2 > 0 and DJ_REF_ANNUELS > 0 and dj_periode > 0 and isinstance(idc_bh_energie_finale_chauffage_comptage_ecs_non_inclus_mj, (int, float))):
            idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_non_inclus_mj_m2 = (
        (idc_bh_energie_finale_chauffage_comptage_ecs_non_inclus_mj / idc_sre_m2)*(DJ_REF_ANNUELS/dj_periode))
        else:
            idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_non_inclus_mj_m2 = 0
    except Exception as e:
        print(e)
        idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_non_inclus_mj_m2 = 0
    return idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_non_inclus_mj_m2

# C124
def fonction_idc_resultat_comptage_ecs_non_inclus_mj_m2(
    idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_non_inclus_mj_m2,
    idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2
):
    """
    IDC = Eh + Eww
    """
    try:
        if idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_non_inclus_mj_m2 > 0 and idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2 > 0:
            idc_resultat_comptage_ecs_non_inclus_mj_m2 = (
                idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_non_inclus_mj_m2 +
                idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2
            )
        else:
            idc_resultat_comptage_ecs_non_inclus_mj_m2 = 0
    except Exception as e:
        print(e)
        idc_resultat_comptage_ecs_non_inclus_mj_m2 = 0
    return idc_resultat_comptage_ecs_non_inclus_mj_m2

# Conversions énergie
    """
    agent_energetique_ef_mazout_somme_mj
    data_site["agent_energetique_ef_gaz_naturel_somme_mj"],
    data_site["agent_energetique_ef_bois_buches_dur_somme_mj"],
    data_site["agent_energetique_ef_bois_buches_tendre_somme_mj"],
    data_site["agent_energetique_ef_pellets_somme_mj"],
    data_site["agent_energetique_ef_plaquettes_somme_mj"],
    data_site["agent_energetique_ef_cad_somme_mj"],
    data_site["agent_energetique_ef_electricite_pac_somme_mj"],
    data_site["agent_energetique_ef_electricite_directe_somme_mj"],
    data_site["agent_energetique_ef_autre_somme_mj"],
    """

def fonction_conversion_energie_idc(
    idc_agent_energetique_ef_cad_reparti_kwh,
    idc_agent_energetique_ef_cad_tarife_kwh,
    idc_agent_energetique_ef_electricite_pac_avant_kwh,
    idc_agent_energetique_ef_electricite_pac_apres_kwh,
    idc_agent_energetique_ef_electricite_directe_kwh,
    idc_agent_energetique_ef_gaz_naturel_m3,
    idc_agent_energetique_ef_gaz_naturel_kwh,
    idc_agent_energetique_ef_mazout_litres,
    idc_agent_energetique_ef_mazout_kg,
    idc_agent_energetique_ef_mazout_kwh,
    idc_agent_energetique_ef_bois_buches_dur_stere,
    idc_agent_energetique_ef_bois_buches_tendre_stere,
    idc_agent_energetique_ef_bois_buches_tendre_kwh,
    idc_agent_energetique_ef_pellets_m3,
    idc_agent_energetique_ef_pellets_kg,
    idc_agent_energetique_ef_pellets_kwh,
    idc_agent_energetique_ef_plaquettes_m3,
    idc_agent_energetique_ef_plaquettes_kwh,
    idc_agent_energetique_ef_autre_kwh,
    idc_ecs_agent_energetique_ef_cad_reparti_kwh,
    idc_ecs_agent_energetique_ef_cad_tarife_kwh,
    idc_ecs_agent_energetique_ef_electricite_pac_avant_kwh,
    idc_ecs_agent_energetique_ef_electricite_pac_apres_kwh,
    idc_ecs_agent_energetique_ef_electricite_directe_kwh,
    idc_ecs_agent_energetique_ef_gaz_naturel_m3,
    idc_ecs_agent_energetique_ef_gaz_naturel_kwh,
    idc_ecs_agent_energetique_ef_mazout_litres,
    idc_ecs_agent_energetique_ef_mazout_kg,
    idc_ecs_agent_energetique_ef_mazout_kwh,
    idc_ecs_agent_energetique_ef_bois_buches_dur_stere,
    idc_ecs_agent_energetique_ef_bois_buches_tendre_stere,
    idc_ecs_agent_energetique_ef_bois_buches_tendre_kwh,
    idc_ecs_agent_energetique_ef_pellets_m3,
    idc_ecs_agent_energetique_ef_pellets_kg,
    idc_ecs_agent_energetique_ef_pellets_kwh,
    idc_ecs_agent_energetique_ef_plaquettes_m3,
    idc_ecs_agent_energetique_ef_plaquettes_kwh,
    idc_ecs_agent_energetique_ef_autre_kwh,
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
    ):
    idc_agent_energetique_ef_mazout_somme_mj = (\
        (idc_agent_energetique_ef_mazout_litres + idc_ecs_agent_energetique_ef_mazout_litres) * IDC_CONVERSION_MAZOUT_MJ_LITRES * IDC_FACTEUR_PONDERATION_MAZOUT +\
        (idc_agent_energetique_ef_mazout_kg + idc_ecs_agent_energetique_ef_mazout_kg) * IDC_CONVERSION_MAZOUT_MJ_KG * IDC_FACTEUR_PONDERATION_MAZOUT +\
        (idc_agent_energetique_ef_mazout_kwh + idc_ecs_agent_energetique_ef_mazout_kwh) * IDC_CONVERSION_MAZOUT_MJ_KWH * IDC_FACTEUR_PONDERATION_MAZOUT\
            )
    idc_agent_energetique_ef_cad_reparti_somme_mj = (\
        (idc_agent_energetique_ef_cad_reparti_kwh + idc_ecs_agent_energetique_ef_cad_reparti_kwh)\
            * IDC_CONVERSION_CAD_REPARTI_MJ_KWH * IDC_FACTEUR_PONDERATION_CAD\
            )
    idc_agent_energetique_ef_cad_tarife_somme_mj = (\
        (idc_agent_energetique_ef_cad_tarife_kwh + idc_ecs_agent_energetique_ef_cad_tarife_kwh)\
            * IDC_CONVERSION_CAD_TARIFE_MJ_KWH * IDC_FACTEUR_PONDERATION_CAD\
            )
    idc_agent_energetique_ef_electricite_pac_avant_somme_mj = (\
        (idc_agent_energetique_ef_electricite_pac_avant_kwh + idc_ecs_agent_energetique_ef_electricite_pac_avant_kwh)\
            * IDC_CONVERSION_ELECTRICITE_PAC_AVANT_MJ_KWH * IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_AVANT\
            )
    idc_agent_energetique_ef_electricite_pac_apres_somme_mj = (\
        (idc_agent_energetique_ef_electricite_pac_apres_kwh + idc_ecs_agent_energetique_ef_electricite_pac_apres_kwh)\
            * IDC_CONVERSION_ELECTRICITE_PAC_APRES_MJ_KWH * IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_APRES\
            )
    idc_agent_energetique_ef_electricite_directe_somme_mj = (\
        (idc_agent_energetique_ef_electricite_directe_kwh + idc_ecs_agent_energetique_ef_electricite_directe_kwh)\
            * IDC_CONVERSION_ELECTRICITE_DIRECTE_MJ_KWH * IDC_FACTEUR_PONDERATION_ELECTRICITE_DIRECTE\
            )
    idc_agent_energetique_ef_gaz_naturel_somme_mj = (\
        (idc_agent_energetique_ef_gaz_naturel_m3 + idc_ecs_agent_energetique_ef_gaz_naturel_m3 ) * IDC_CONVERSION_GAZ_NATUREL_MJ_M3 * IDC_FACTEUR_PONDERATION_GAZ_NATUREL +\
            (idc_agent_energetique_ef_gaz_naturel_kwh + idc_ecs_agent_energetique_ef_gaz_naturel_kwh) * IDC_CONVERSION_GAZ_NATUREL_MJ_KWH * IDC_FACTEUR_PONDERATION_GAZ_NATUREL\
            )

    idc_agent_energetique_ef_bois_buches_dur_somme_mj = (\
        (idc_agent_energetique_ef_bois_buches_dur_stere + idc_ecs_agent_energetique_ef_bois_buches_dur_stere) * IDC_CONVERSION_BOIS_BUCHES_DUR_MJ_STERE * IDC_FACTEUR_PONDERATION_BOIS_BUCHES_DUR\
            )
    idc_agent_energetique_ef_bois_buches_tendre_somme_mj = (\
        (idc_agent_energetique_ef_bois_buches_tendre_stere + idc_ecs_agent_energetique_ef_bois_buches_tendre_stere) * IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_STERE * IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE +\
        (idc_agent_energetique_ef_bois_buches_tendre_kwh + idc_ecs_agent_energetique_ef_bois_buches_tendre_kwh) * IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_KWH * IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE\
            )
    idc_agent_energetique_ef_pellets_somme_mj = (\
        (idc_agent_energetique_ef_pellets_m3 + idc_ecs_agent_energetique_ef_pellets_m3) * IDC_CONVERSION_PELLETS_MJ_M3 * IDC_FACTEUR_PONDERATION_PELLETS +\
        (idc_agent_energetique_ef_pellets_kg + idc_ecs_agent_energetique_ef_pellets_kg) * IDC_CONVERSION_PELLETS_MJ_KG * IDC_FACTEUR_PONDERATION_PELLETS +\
        (idc_agent_energetique_ef_pellets_kwh + idc_ecs_agent_energetique_ef_pellets_kwh) * IDC_CONVERSION_PELLETS_MJ_KWH * IDC_FACTEUR_PONDERATION_PELLETS\
            )
    idc_agent_energetique_ef_plaquettes_somme_mj = (\
        (idc_agent_energetique_ef_plaquettes_m3 + idc_ecs_agent_energetique_ef_plaquettes_m3) * IDC_CONVERSION_PLAQUETTES_MJ_M3 * IDC_FACTEUR_PONDERATION_PLAQUETTES +\
        (idc_agent_energetique_ef_plaquettes_kwh + idc_ecs_agent_energetique_ef_plaquettes_kwh) * IDC_CONVERSION_PLAQUETTES_MJ_KWH * IDC_FACTEUR_PONDERATION_PLAQUETTES\
            )
    idc_agent_energetique_ef_autre_somme_mj = (\
        (idc_agent_energetique_ef_autre_kwh + idc_ecs_agent_energetique_ef_autre_kwh) * IDC_CONVERSION_AUTRE_MJ_KWH * IDC_FACTEUR_PONDERATION_AUTRE\
            )
    
    return (
        idc_agent_energetique_ef_mazout_somme_mj,
        idc_agent_energetique_ef_gaz_naturel_somme_mj,
        idc_agent_energetique_ef_bois_buches_dur_somme_mj,
        idc_agent_energetique_ef_bois_buches_tendre_somme_mj,
        idc_agent_energetique_ef_pellets_somme_mj,
        idc_agent_energetique_ef_plaquettes_somme_mj,
        idc_agent_energetique_ef_cad_reparti_somme_mj,
        idc_agent_energetique_ef_cad_tarife_somme_mj,
        idc_agent_energetique_ef_electricite_pac_avant_somme_mj,
        idc_agent_energetique_ef_electricite_pac_apres_somme_mj,
        idc_agent_energetique_ef_electricite_directe_somme_mj,
        idc_agent_energetique_ef_autre_somme_mj
    )