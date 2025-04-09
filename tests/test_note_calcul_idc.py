# test_note_calcul_idc.py

# import pytest
from pytest import approx

# import pandas as pd
from datetime import datetime
import sys
import os

# Add the parent directory to sys.path to import the functions
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sections.helpers.calcul_dj import (
    get_meteo_data,
    calcul_dj_periode,
)

from sections.helpers.note_calcul.calculs_idc import (
    fonction_idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2,
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

# Get the meteorological data
df_meteo_tre200d0 = get_meteo_data()

####################################################################################################

# Test data for the functions
# test_1 (Avusy)
test_1_in = {
    'comptage_ecs_inclus': True,
    "idc_sre_m2": 20000.0,
    "periode_start": datetime(2024, 1, 1),
    "periode_end": datetime(2025, 1, 1),
    "periode_nb_jours": 367,
    'sre_pourcentage_habitat_collectif': 60.0,
    'sre_pourcentage_habitat_individuel': 0.0,
    'sre_pourcentage_administration': 10.0,
    'sre_pourcentage_ecoles': 10.0,
    'sre_pourcentage_commerce': 10.0,
    'sre_pourcentage_restauration': 10.0,
    'sre_pourcentage_lieux_de_rassemblement': 0.0,
    'sre_pourcentage_hopitaux': 0.0,
    'sre_pourcentage_industrie': 0.0,
    'sre_pourcentage_depots': 0.0,
    'sre_pourcentage_installations_sportives': 0.0,
    'sre_pourcentage_piscines_couvertes': 0.0,
    'idc_agent_energetique_ef_mazout_litres': 1000.0,
    'idc_agent_energetique_ef_mazout_kg': 1000.0,
    'idc_agent_energetique_ef_mazout_kwh': 1000.0,
    'idc_agent_energetique_ef_gaz_naturel_m3': 1000.0,
    'idc_agent_energetique_ef_gaz_naturel_kwh': 1000.0,
    'idc_agent_energetique_ef_bois_buches_dur_stere': 1000.0,
    'idc_agent_energetique_ef_bois_buches_tendre_stere': 1000.0,
    'idc_agent_energetique_ef_bois_buches_tendre_kwh': 1000.0,
    'idc_agent_energetique_ef_pellets_m3': 1000.0,
    'idc_agent_energetique_ef_pellets_kg': 1000.0,
    'idc_agent_energetique_ef_pellets_kwh': 1000.0,
    'idc_agent_energetique_ef_plaquettes_m3': 1000.0,
    'idc_agent_energetique_ef_plaquettes_kwh': 1000.0,
    'idc_agent_energetique_ef_cad_tarife_kwh': 1000.0,
    'idc_agent_energetique_ef_cad_reparti_kwh': 1000.0,
    'idc_agent_energetique_ef_electricite_pac_avant_kwh': 1000.0,
    'idc_agent_energetique_ef_electricite_pac_apres_kwh': 1000.0,
    'idc_agent_energetique_ef_electricite_directe_kwh': 1000.0,
    'idc_agent_energetique_ef_autre_kwh': 1000.0,
}

test_1_out = {
    "dj_periode": 2961.8,
    "idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2": 123.90,
}

# combine the 2 dictionaries in data_site_avusy1
data_site_1 = {**test_1_in, **test_1_out}


# calcul_dj.py
def test_calcul_dj_periode():
    assert (
        calcul_dj_periode(
            df_meteo_tre200d0,
            data_site_1["periode_start"],
            data_site_1["periode_end"],
        )
        == data_site_1["dj_periode"]
    )
    assert (
        calcul_dj_periode(
            df_meteo_tre200d0,
            datetime(2023, 1, 1),
            datetime(2024, 1, 1),
        )
        == 2804.3
    )


# note_calcul_idc.py
def test_fonction_idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2():
    assert fonction_idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2(
        data_site_1["sre_pourcentage_habitat_collectif"],
        data_site_1["sre_pourcentage_habitat_individuel"],
        data_site_1["sre_pourcentage_administration"],
        data_site_1["sre_pourcentage_ecoles"],
        data_site_1["sre_pourcentage_commerce"],
        data_site_1["sre_pourcentage_restauration"],
        data_site_1["sre_pourcentage_lieux_de_rassemblement"],
        data_site_1["sre_pourcentage_hopitaux"],
        data_site_1["sre_pourcentage_industrie"],
        data_site_1["sre_pourcentage_depots"],
        data_site_1["sre_pourcentage_installations_sportives"],
        data_site_1["sre_pourcentage_piscines_couvertes"],
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
    ) == approx(data_site_1["idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2"])

