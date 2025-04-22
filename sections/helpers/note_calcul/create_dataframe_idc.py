# sections/helpers/note_calcul/create_dataframe_idc.py

import pandas as pd

def make_dataframe_df_list_idc(data_site, DJ_REF_ANNUELS):
    df_list = []

    columns = [
        "Dénomination",
        "Valeur",
        "Unité",
        "Variante ECS",
        "Commentaire",
        "Excel",
        "Variable",
    ]

    # C67 → Nombre de jours
    df_list.append(
        {
            "Dénomination": "Nombre de jour(s)",
            "Valeur": data_site["periode_nb_jours"],
            "Unité": "jour(s)",
            "Variante ECS": "Toutes",
            "Commentaire": "Nombre de jour(s) dans la période",
            "Excel": "C67",
            "Variable": "periode_nb_jours",
        }
    )

    # C117 → Variante calcul ECS avec/sans comptage séparé
    df_list.append(
        {
            "Dénomination": "Variante calcul ECS avec/sans comptage séparé",
            "Valeur": data_site["comptage_ecs_inclus"],
            "Unité": "",
            "Variante ECS": "Toutes",
            "Commentaire": "True (1) si comptage inclus, False (0) séparé",
            "Excel": "C117",
            "Variable": "comptage_ecs_inclus",
        }
    )

    # Variante comptage_ecs_inclus True
    
    # C118 → IDC_Bww → Energie finale pour l'ECS
    df_list.append(
        {
            "Dénomination": "IDC_Bww",
            "Valeur": data_site["idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj"],
            "Unité": "MJ",
            "Variante ECS": "Comptage ECS inclus",
            "Commentaire": "Energie finale pour l'ECS",
            "Excel": "C118",
            "Variable": "idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj",
        }
    )
    # C119 → IDC_Eww → Part d'énergie finale pour ECS
    df_list.append(
        {
            "Dénomination": "IDC_Eww",
            "Valeur": data_site["idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2"],
            "Unité": "MJ/m²",
            "Variante ECS": "Comptage ECS inclus",
            "Commentaire": "Part d'énergie finale pour ECS",
            "Excel": "C119",
            "Variable": "idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2",
        }
    )
    # C120 → IDC_Bh → Part chauffage de l'énergie finale
    df_list.append(
        {
            "Dénomination": "IDC_Bh",
            "Valeur": data_site["idc_bh_energie_finale_chauffage_comptage_ecs_inclus_mj"],
            "Unité": "MJ",
            "Variante ECS": "Comptage ECS inclus",
            "Commentaire": "Part chauffage de l'énergie finale",
            "Excel": "C120",
            "Variable": "idc_bh_energie_finale_chauffage_comptage_ecs_inclus_mj",
        }
    )
    # C121 → DJ ref annuels
    df_list.append(
        {
            "Dénomination": "DJ réference annuels",
            "Valeur": DJ_REF_ANNUELS,
            "Unité": "degrés-jour",
            "Variante ECS": "Toutes",
            "Commentaire": "Degrés-jour de référence annuels selon SIA 2028",
            "Excel": "C121",
            "Variable": "DJ_REF_ANNUELS",
        }
    )

    # C122 → DJ période
    df_list.append(
        {
            "Dénomination": "DJ période",
            "Valeur": data_site["dj_periode"],
            "Unité": "degrés-jour",
            "Variante ECS": "Toutes",
            "Commentaire": "Degrés-jour dans la période",
            "Excel": "C122",
            "Variable": "dj_periode",
        }
    )

    # C123 → IDC_Eh → Part d'énergie finale pour le chauffage avec correction climatique
    df_list.append(
        {
            "Dénomination": "IDC_Eh",
            "Valeur": data_site["idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_inclus_mj_m2"],
            "Unité": "MJ/m²",
            "Variante ECS": "Comptage ECS inclus",
            "Commentaire": "Part d'énergie finale pour le chauffage avec correction climatique",
            "Excel": "C123",
            "Variable": "idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_inclus_mj_m2",
        }
    )

    # C124 → IDC_Eh + IDC_Eww
    df_list.append(
        {
            "Dénomination": "IDC",
            "Valeur": data_site["idc_resultat_comptage_ecs_inclus_mj_m2"]
            + data_site["idc_eww_theorique_moyen_comptage_ecs_inclus_mj_m2"],
            "Unité": "MJ/m²",
            "Variante ECS": "Comptage ECS inclus",
            "Commentaire": "IDC = IDC_Eh + IDC_Eww",
            "Excel": "C124",
            "Variable": "idc_resultat_comptage_ecs_inclus_mj_m2",
        }
    )

    # Variante comptage_ecs_inclus False
    
    # C118 → IDC_Bww → Energie finale pour l'ECS
    df_list.append(
        {
            "Dénomination": "IDC_Bww (ECS séparé)",
            "Valeur": data_site["idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj"],
            "Unité": "MJ",
            "Variante ECS": "Comptage ECS séparé",
            "Commentaire": "Energie finale pour l'ECS",
            "Excel": "C118",
            "Variable": "idc_bww_energie_finale_ecs_comptage_ecs_non_inclus_mj",
        }
    )

    """
    data_site["idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_non_inclus_mj_m2"] = 0
    data_site["idc_resultat_comptage_ecs_non_inclus_mj_m2"] = 0
    """

    # C119 → IDC_Eww → Part d'énergie finale pour ECS
    df_list.append(
        {
            "Dénomination": "IDC_Eww (ECS séparé)",
            "Valeur": data_site["idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2"],
            "Unité": "MJ/m²",
            "Variante ECS": "Comptage ECS séparé",
            "Commentaire": "Part d'énergie finale pour ECS",
            "Excel": "C119",
            "Variable": "idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2",
        }
    )

    # C120 → IDC_Bh → Part chauffage de l'énergie finale
    df_list.append(
        {
            "Dénomination": "IDC_Bh (ECS séparé)",
            "Valeur": data_site["idc_bh_energie_finale_chauffage_comptage_ecs_non_inclus_mj"],
            "Unité": "MJ",
            "Variante ECS": "Comptage ECS séparé",
            "Commentaire": "Part chauffage de l'énergie finale",
            "Excel": "C120",
            "Variable": "idc_bh_energie_finale_chauffage_comptage_ecs_non_inclus_mj",
        }
    )

    # C123 → IDC_Eh → Part d'énergie finale pour le chauffage avec correction climatique
    df_list.append(
        {
            "Dénomination": "IDC_Eh (ECS séparé)",
            "Valeur": data_site["idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_non_inclus_mj_m2"],
            "Unité": "MJ/m²",
            "Variante ECS": "Comptage ECS séparé",
            "Commentaire": "Part d'énergie finale pour le chauffage avec correction climatique",
            "Excel": "C123",
            "Variable": "idc_eh_part_energie_finale_chauffage_climatiquement_corrige_comptage_ecs_non_inclus_mj_m2",
        }
    )

    # C124 → IDC_Eh + IDC_Eww
    df_list.append(
        {
            "Dénomination": "IDC (ECS séparé)",
            "Valeur": data_site["idc_resultat_comptage_ecs_non_inclus_mj_m2"]
            + data_site["idc_eww_part_energie_finale_ecs_comptage_ecs_non_inclus_mj_m2"],
            "Unité": "MJ/m²",
            "Variante ECS": "Comptage ECS séparé",
            "Commentaire": "IDC (ECS séparé) = IDC_Eh (ECS séparé) + IDC_Eww (ECS séparé)",
            "Excel": "C124",
            "Variable": "idc_resultat_comptage_ecs_non_inclus_mj_m2",
        }
    )

    return pd.DataFrame(df_list, columns=columns)


def make_dataframe_df_agent_energetique_idc(
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
    IDC_FACTEUR_PONDERATION_AUTRE,
):
    df_agent_energetique_idc_sum = pd.DataFrame(
        {
            "Agent énergétique": [
                "Mazout",
                "Gaz naturel",
                "Bois (buches dur)",
                "Bois (buches tendre)",
                "Pellets",
                "Plaquettes",
                "CAD (réparti)",
                "CAD (tarifé)",
                "Electricité (PAC avant)",
                "Electricité (PAC après)",
                "Electricité (directe)",
                "Autre",
            ],
            "Somme MJ (fp inclus)": [
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
                data_site["idc_agent_energetique_ef_autre_somme_mj"],
            ],
            "Somme kWh (fp inclus)": [
                data_site["idc_agent_energetique_ef_mazout_somme_mj"] / 3.6,
                data_site["idc_agent_energetique_ef_gaz_naturel_somme_mj"] / 3.6,
                data_site["idc_agent_energetique_ef_bois_buches_dur_somme_mj"] / 3.6,
                data_site["idc_agent_energetique_ef_bois_buches_tendre_somme_mj"] / 3.6,
                data_site["idc_agent_energetique_ef_pellets_somme_mj"] / 3.6,
                data_site["idc_agent_energetique_ef_plaquettes_somme_mj"] / 3.6,
                data_site["idc_agent_energetique_ef_cad_reparti_somme_mj"] / 3.6,
                data_site["idc_agent_energetique_ef_cad_tarife_somme_mj"] / 3.6,
                data_site["idc_agent_energetique_ef_electricite_pac_avant_somme_mj"] / 3.6,
                data_site["idc_agent_energetique_ef_electricite_pac_apres_somme_mj"] / 3.6,
                data_site["idc_agent_energetique_ef_electricite_directe_somme_mj"] / 3.6,
                data_site["idc_agent_energetique_ef_autre_somme_mj"] / 3.6,
            ],
            "Facteur de pondération": [
            IDC_FACTEUR_PONDERATION_MAZOUT,
            IDC_FACTEUR_PONDERATION_GAZ_NATUREL,
            IDC_FACTEUR_PONDERATION_BOIS_BUCHES_DUR,
            IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE,
            IDC_FACTEUR_PONDERATION_PELLETS,
            IDC_FACTEUR_PONDERATION_PLAQUETTES,
            IDC_FACTEUR_PONDERATION_CAD,
            IDC_FACTEUR_PONDERATION_CAD,
            IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_AVANT,
            IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_APRES,
            IDC_FACTEUR_PONDERATION_ELECTRICITE_DIRECTE,
            IDC_FACTEUR_PONDERATION_AUTRE,
            ],
            "Variable Agent énergétique": [
                "idc_agent_energetique_ef_mazout_somme_mj",
                "idc_agent_energetique_ef_gaz_naturel_somme_mj",
                "idc_agent_energetique_ef_bois_buches_dur_somme_mj",
                "idc_agent_energetique_ef_bois_buches_tendre_somme_mj",
                "idc_agent_energetique_ef_pellets_somme_mj",
                "idc_agent_energetique_ef_plaquettes_somme_mj",
                "idc_agent_energetique_ef_cad_reparti_somme_mj",
                "idc_agent_energetique_ef_cad_tarife_somme_mj",
                "idc_agent_energetique_ef_electricite_pac_avant_somme_mj",
                "idc_agent_energetique_ef_electricite_pac_apres_somme_mj",
                "idc_agent_energetique_ef_electricite_directe_somme_mj",
                "idc_agent_energetique_ef_autre_somme_mj",
            ],
            "Variable facteur de pondération": [
                "IDC_FACTEUR_PONDERATION_MAZOUT",
                "IDC_FACTEUR_PONDERATION_GAZ_NATUREL",
                "IDC_FACTEUR_PONDERATION_BOIS_BUCHES_DUR",
                "IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE",
                "IDC_FACTEUR_PONDERATION_PELLETS",
                "IDC_FACTEUR_PONDERATION_PLAQUETTES",
                "IDC_FACTEUR_PONDERATION_CAD",
                "IDC_FACTEUR_PONDERATION_CAD",
                "IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_AVANT",
                "IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_APRES",
                "IDC_FACTEUR_PONDERATION_ELECTRICITE_DIRECTE",
                "IDC_FACTEUR_PONDERATION_AUTRE",
            ],
        }
    )
    
    df_agent_energetique_idc_mazout = pd.DataFrame(
            {
                "Agent énergétique": [
                    "Mazout (litres)",
                    "Mazout (kg)",
                    "Mazout (kWh)",
                    "Total Mazout (MJ)"
                ],
                "Quantité renseignée": [
                    str(data_site.get("idc_agent_energetique_ef_mazout_litres", 0)),
                    str(data_site.get("idc_agent_energetique_ef_mazout_kg", 0)),
                    str(data_site.get("idc_agent_energetique_ef_mazout_kwh", 0)),
                    "-"
                ],
                "Unité": [
                    "litres",
                    "kg",
                    "kWh",
                    "MJ"
                ],
                "Facteur conversion MJ": [
                    str(IDC_CONVERSION_MAZOUT_MJ_LITRES),
                    str(IDC_CONVERSION_MAZOUT_MJ_KG),
                    str(IDC_CONVERSION_MAZOUT_MJ_KWH),
                    "-"
                ],
                "Énergie (MJ)": [
                    data_site.get("idc_agent_energetique_ef_mazout_litres", 0) * IDC_CONVERSION_MAZOUT_MJ_LITRES,
                    data_site.get("idc_agent_energetique_ef_mazout_kg", 0) * IDC_CONVERSION_MAZOUT_MJ_KG,
                    data_site.get("idc_agent_energetique_ef_mazout_kwh", 0) * IDC_CONVERSION_MAZOUT_MJ_KWH,
                    data_site.get("idc_agent_energetique_ef_mazout_somme_mj", 0)/IDC_FACTEUR_PONDERATION_MAZOUT,
                ],
                "Facteur pondération": [
                    IDC_FACTEUR_PONDERATION_MAZOUT,
                    IDC_FACTEUR_PONDERATION_MAZOUT,
                    IDC_FACTEUR_PONDERATION_MAZOUT,
                    IDC_FACTEUR_PONDERATION_MAZOUT,
                ],
                "Énergie pondérée (MJ)": [
                    data_site.get("idc_agent_energetique_ef_mazout_litres", 0) * IDC_CONVERSION_MAZOUT_MJ_LITRES * IDC_FACTEUR_PONDERATION_MAZOUT,
                    data_site.get("idc_agent_energetique_ef_mazout_kg", 0) * IDC_CONVERSION_MAZOUT_MJ_KG * IDC_FACTEUR_PONDERATION_MAZOUT,
                    data_site.get("idc_agent_energetique_ef_mazout_kwh", 0) * IDC_CONVERSION_MAZOUT_MJ_KWH * IDC_FACTEUR_PONDERATION_MAZOUT,
                    data_site.get("idc_agent_energetique_ef_mazout_somme_mj", 0)/IDC_FACTEUR_PONDERATION_MAZOUT * IDC_FACTEUR_PONDERATION_MAZOUT,
                ]
            }
        )

    df_agent_energetique_idc_gaz_naturel = pd.DataFrame(
            {
                "Agent énergétique": [
                    "Gaz naturel (m3)",
                    "Gaz naturel (kWh)",
                    "Total Gaz naturel (MJ)"
                ],
                "Quantité renseignée": [
                    str(data_site.get("idc_agent_energetique_ef_gaz_naturel_m3", 0)),
                    str(data_site.get("idc_agent_energetique_ef_gaz_naturel_kwh", 0)),
                    "-"
                ],
                "Unité": [
                    "m3",
                    "kWh",
                    "MJ"
                ],
                "Facteur conversion MJ": [
                    str(IDC_CONVERSION_GAZ_NATUREL_MJ_M3),
                    str(IDC_CONVERSION_GAZ_NATUREL_MJ_KWH),
                    "-"
                ],
                "Énergie (MJ)": [
                    data_site.get("idc_agent_energetique_ef_gaz_naturel_m3", 0) * IDC_CONVERSION_GAZ_NATUREL_MJ_M3,
                    data_site.get("idc_agent_energetique_ef_gaz_naturel_kwh", 0) * IDC_CONVERSION_GAZ_NATUREL_MJ_KWH,
                    data_site.get("idc_agent_energetique_ef_gaz_naturel_somme_mj", 0)/IDC_FACTEUR_PONDERATION_GAZ_NATUREL,
                ],
                "Facteur pondération": [
                    IDC_FACTEUR_PONDERATION_GAZ_NATUREL,
                    IDC_FACTEUR_PONDERATION_GAZ_NATUREL,
                    IDC_FACTEUR_PONDERATION_GAZ_NATUREL,
                ],
                "Énergie pondérée (MJ)": [
                    data_site.get("idc_agent_energetique_ef_gaz_naturel_m3", 0) * IDC_CONVERSION_GAZ_NATUREL_MJ_M3 * IDC_FACTEUR_PONDERATION_GAZ_NATUREL,
                    data_site.get("idc_agent_energetique_ef_gaz_naturel_kwh", 0) * IDC_CONVERSION_GAZ_NATUREL_MJ_KWH * IDC_FACTEUR_PONDERATION_GAZ_NATUREL,
                    data_site.get("idc_agent_energetique_ef_gaz_naturel_somme_mj", 0),
                ]
            }
        )

    df_agent_energetique_idc_bois_buches_dur = pd.DataFrame(
            {
                "Agent énergétique": [
                    "Bois (buches dur) (stère)",
                    "Bois (buches dur) (kWh)",
                    "Total Bois (buches dur) (MJ)"
                ],
                "Quantité renseignée": [
                    str(data_site.get("idc_agent_energetique_ef_bois_buches_dur_stere", 0)),
                    str(data_site.get("idc_agent_energetique_ef_bois_buches_dur_kwh", 0)),
                    "-"
                ],
                "Unité": [
                    "stère",
                    "kWh",
                    "MJ"
                ],
                "Facteur conversion MJ": [
                    str(IDC_CONVERSION_BOIS_BUCHES_DUR_MJ_STERE),
                    str(IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_KWH),
                    "-"
                ],
                "Énergie (MJ)": [
                    data_site.get("idc_agent_energetique_ef_bois_buches_dur_stere", 0) * IDC_CONVERSION_BOIS_BUCHES_DUR_MJ_STERE,
                    data_site.get("idc_agent_energetique_ef_bois_buches_dur_kwh", 0) * IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_KWH,
                    data_site.get("idc_agent_energetique_ef_bois_buches_dur_somme_mj", 0)/IDC_FACTEUR_PONDERATION_BOIS_BUCHES_DUR,
                ],
                "Facteur pondération": [
                    IDC_FACTEUR_PONDERATION_BOIS_BUCHES_DUR,
                    IDC_FACTEUR_PONDERATION_BOIS_BUCHES_DUR,
                    IDC_FACTEUR_PONDERATION_BOIS_BUCHES_DUR,
                ],
                "Énergie pondérée (MJ)": [
                    data_site.get("idc_agent_energetique_ef_bois_buches_dur_stere", 0) * IDC_CONVERSION_BOIS_BUCHES_DUR_MJ_STERE * IDC_FACTEUR_PONDERATION_BOIS_BUCHES_DUR,
                    data_site.get("idc_agent_energetique_ef_bois_buches_dur_kwh", 0) * IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_KWH * IDC_FACTEUR_PONDERATION_BOIS_BUCHES_DUR,
                    data_site.get("idc_agent_energetique_ef_bois_buches_dur_somme_mj", 0),
                ]
            }
        )

    df_agent_energetique_idc_bois_buches_tendre = pd.DataFrame(
        {
            "Agent énergétique": [
                "Bois (buches tendre) (stère)",
                "Bois (buches tendre) (kWh)",
                "Total Bois (buches tendre) (MJ)"
            ],
            "Quantité renseignée": [
                str(data_site.get("idc_agent_energetique_ef_bois_buches_tendre_stere", 0)),
                str(data_site.get("idc_agent_energetique_ef_bois_buches_tendre_kwh", 0)),
                "-"
            ],
            "Unité": [
                "stère",
                "kWh",
                "MJ"
            ],
            "Facteur conversion MJ": [
                str(IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_STERE),
                str(IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_KWH),
                "-"
            ],
            "Énergie (MJ)": [
                data_site.get("idc_agent_energetique_ef_bois_buches_tendre_stere", 0) * IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_STERE,
                data_site.get("idc_agent_energetique_ef_bois_buches_tendre_kwh", 0) * IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_KWH,
                data_site.get("idc_agent_energetique_ef_bois_buches_tendre_somme_mj", 0) / IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE,
            ],
            "Facteur pondération": [
                IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE,
                IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE,
                IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE,
            ],
            "Énergie pondérée (MJ)": [
                data_site.get("idc_agent_energetique_ef_bois_buches_tendre_stere", 0) * IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_STERE * IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE,
                data_site.get("idc_agent_energetique_ef_bois_buches_tendre_kwh", 0) * IDC_CONVERSION_BOIS_BUCHES_TENDRE_MJ_KWH * IDC_FACTEUR_PONDERATION_BOIS_BUCHES_TENDRE,
                data_site.get("idc_agent_energetique_ef_bois_buches_tendre_somme_mj", 0),
            ]
        }
    )

    df_agent_energetique_idc_pellets = pd.DataFrame(
        {
            "Agent énergétique": [
                "Pellets (m3)",
                "Pellets (kg)",
                "Pellets (kWh)",
                "Total Pellets (MJ)"
            ],
            "Quantité renseignée": [
                str(data_site.get("idc_agent_energetique_ef_pellets_m3", 0)),
                str(data_site.get("idc_agent_energetique_ef_pellets_kg", 0)),
                str(data_site.get("idc_agent_energetique_ef_pellets_kwh", 0)),
                "-"
            ],
            "Unité": [
                "m3",
                "kg",
                "kWh",
                "MJ"
            ],
            "Facteur conversion MJ": [
                str(IDC_CONVERSION_PELLETS_MJ_M3),
                str(IDC_CONVERSION_PELLETS_MJ_KG),
                str(IDC_CONVERSION_PELLETS_MJ_KWH),
                "-"
            ],
            "Énergie (MJ)": [
                data_site.get("idc_agent_energetique_ef_pellets_m3", 0) * IDC_CONVERSION_PELLETS_MJ_M3,
                data_site.get("idc_agent_energetique_ef_pellets_kg", 0) * IDC_CONVERSION_PELLETS_MJ_KG,
                data_site.get("idc_agent_energetique_ef_pellets_kwh", 0) * IDC_CONVERSION_PELLETS_MJ_KWH,
                data_site.get("idc_agent_energetique_ef_pellets_somme_mj", 0) / IDC_FACTEUR_PONDERATION_PELLETS,
            ],
            "Facteur pondération": [
                IDC_FACTEUR_PONDERATION_PELLETS,
                IDC_FACTEUR_PONDERATION_PELLETS,
                IDC_FACTEUR_PONDERATION_PELLETS,
                IDC_FACTEUR_PONDERATION_PELLETS,
            ],
            "Énergie pondérée (MJ)": [
                data_site.get("idc_agent_energetique_ef_pellets_m3", 0) * IDC_CONVERSION_PELLETS_MJ_M3 * IDC_FACTEUR_PONDERATION_PELLETS,
                data_site.get("idc_agent_energetique_ef_pellets_kg", 0) * IDC_CONVERSION_PELLETS_MJ_KG * IDC_FACTEUR_PONDERATION_PELLETS,
                data_site.get("idc_agent_energetique_ef_pellets_kwh", 0) * IDC_CONVERSION_PELLETS_MJ_KWH * IDC_FACTEUR_PONDERATION_PELLETS,
                data_site.get("idc_agent_energetique_ef_pellets_somme_mj", 0),
            ]
        }
    )

    df_agent_energetique_idc_plaquettes = pd.DataFrame(
        {
            "Agent énergétique": [
                "Plaquettes (m3)",
                "Plaquettes (kWh)",
                "Total Plaquettes (MJ)"
            ],
            "Quantité renseignée": [
                str(data_site.get("idc_agent_energetique_ef_plaquettes_m3", 0)),
                str(data_site.get("idc_agent_energetique_ef_plaquettes_kwh", 0)),
                "-"
            ],
            "Unité": [
                "m3",
                "kWh",
                "MJ"
            ],
            "Facteur conversion MJ": [
                str(IDC_CONVERSION_PLAQUETTES_MJ_M3),
                str(IDC_CONVERSION_PLAQUETTES_MJ_KWH),
                "-"
            ],
            "Énergie (MJ)": [
                data_site.get("idc_agent_energetique_ef_plaquettes_m3", 0) * IDC_CONVERSION_PLAQUETTES_MJ_M3,
                data_site.get("idc_agent_energetique_ef_plaquettes_kwh", 0) * IDC_CONVERSION_PLAQUETTES_MJ_KWH,
                data_site.get("idc_agent_energetique_ef_plaquettes_somme_mj", 0) / IDC_FACTEUR_PONDERATION_PLAQUETTES,
            ],
            "Facteur pondération": [
                IDC_FACTEUR_PONDERATION_PLAQUETTES,
                IDC_FACTEUR_PONDERATION_PLAQUETTES,
                IDC_FACTEUR_PONDERATION_PLAQUETTES,
            ],
            "Énergie pondérée (MJ)": [
                data_site.get("idc_agent_energetique_ef_plaquettes_m3", 0) * IDC_CONVERSION_PLAQUETTES_MJ_M3 * IDC_FACTEUR_PONDERATION_PLAQUETTES,
                data_site.get("idc_agent_energetique_ef_plaquettes_kwh", 0) * IDC_CONVERSION_PLAQUETTES_MJ_KWH * IDC_FACTEUR_PONDERATION_PLAQUETTES,
                data_site.get("idc_agent_energetique_ef_plaquettes_somme_mj", 0),
            ]
        }
    )

    df_agent_energetique_idc_cad_reparti = pd.DataFrame(
        {
            "Agent énergétique": [
                "CAD (réparti) (kWh)",
                "Total CAD (réparti) (MJ)"
            ],
            "Quantité renseignée": [
                str(data_site.get("idc_agent_energetique_ef_cad_reparti_kwh", 0)),
                "-"
            ],
            "Unité": [
                "kWh",
                "MJ"
            ],
            "Facteur conversion MJ": [
                str(IDC_CONVERSION_CAD_REPARTI_MJ_KWH),
                "-"
            ],
            "Énergie (MJ)": [
                data_site.get("idc_agent_energetique_ef_cad_reparti_kwh", 0) * IDC_CONVERSION_CAD_REPARTI_MJ_KWH,
                data_site.get("idc_agent_energetique_ef_cad_reparti_somme_mj", 0) / IDC_FACTEUR_PONDERATION_CAD,
            ],
            "Facteur pondération": [
                IDC_FACTEUR_PONDERATION_CAD,
                IDC_FACTEUR_PONDERATION_CAD,
            ],
            "Énergie pondérée (MJ)": [
                data_site.get("idc_agent_energetique_ef_cad_reparti_kwh", 0) * IDC_CONVERSION_CAD_REPARTI_MJ_KWH * IDC_FACTEUR_PONDERATION_CAD,
                data_site.get("idc_agent_energetique_ef_cad_reparti_somme_mj", 0),
            ]
        }
    )

    df_agent_energetique_idc_cad_tarife = pd.DataFrame(
        {
            "Agent énergétique": [
                "CAD (tarifé) (kWh)",
                "Total CAD (tarifé) (MJ)"
            ],
            "Quantité renseignée": [
                str(data_site.get("idc_agent_energetique_ef_cad_tarife_kwh", 0)),
                "-"
            ],
            "Unité": [
                "kWh",
                "MJ"
            ],
            "Facteur conversion MJ": [
                str(IDC_CONVERSION_CAD_TARIFE_MJ_KWH),
                "-"
            ],
            "Énergie (MJ)": [
                data_site.get("idc_agent_energetique_ef_cad_tarife_kwh", 0) * IDC_CONVERSION_CAD_TARIFE_MJ_KWH,
                data_site.get("idc_agent_energetique_ef_cad_tarife_somme_mj", 0) / IDC_FACTEUR_PONDERATION_CAD,
            ],
            "Facteur pondération": [
                IDC_FACTEUR_PONDERATION_CAD,
                IDC_FACTEUR_PONDERATION_CAD,
            ],
            "Énergie pondérée (MJ)": [
                data_site.get("idc_agent_energetique_ef_cad_tarife_kwh", 0) * IDC_CONVERSION_CAD_TARIFE_MJ_KWH * IDC_FACTEUR_PONDERATION_CAD,
                data_site.get("idc_agent_energetique_ef_cad_tarife_somme_mj", 0),
            ]
        }
    )

    df_agent_energetique_idc_electricite_pac_avant = pd.DataFrame(
        {
            "Agent énergétique": [
                "Electricité (PAC avant) (kWh)",
                "Total Electricité (PAC avant) (MJ)"
            ],
            "Quantité renseignée": [
                str(data_site.get("idc_agent_energetique_ef_electricite_pac_avant_kwh", 0)),
                "-"
            ],
            "Unité": [
                "kWh",
                "MJ"
            ],
            "Facteur conversion MJ": [
                str(IDC_CONVERSION_ELECTRICITE_PAC_AVANT_MJ_KWH),
                "-"
            ],
            "Énergie (MJ)": [
                data_site.get("idc_agent_energetique_ef_electricite_pac_avant_kwh", 0) * IDC_CONVERSION_ELECTRICITE_PAC_AVANT_MJ_KWH,
                data_site.get("idc_agent_energetique_ef_electricite_pac_avant_somme_mj", 0) / IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_AVANT,
            ],
            "Facteur pondération": [
                IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_AVANT,
                IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_AVANT,
            ],
            "Énergie pondérée (MJ)": [
                data_site.get("idc_agent_energetique_ef_electricite_pac_avant_kwh", 0) * IDC_CONVERSION_ELECTRICITE_PAC_AVANT_MJ_KWH * IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_AVANT,
                data_site.get("idc_agent_energetique_ef_electricite_pac_avant_somme_mj", 0),
            ]
        }
    )

    df_agent_energetique_idc_electricite_pac_apres = pd.DataFrame(
        {
            "Agent énergétique": [
                "Electricité (PAC après) (kWh)",
                "Total Electricité (PAC après) (MJ)"
            ],
            "Quantité renseignée": [
                str(data_site.get("idc_agent_energetique_ef_electricite_pac_apres_kwh", 0)),
                "-"
            ],
            "Unité": [
                "kWh",
                "MJ"
            ],
            "Facteur conversion MJ": [
                str(IDC_CONVERSION_ELECTRICITE_PAC_APRES_MJ_KWH),
                "-"
            ],
            "Énergie (MJ)": [
                data_site.get("idc_agent_energetique_ef_electricite_pac_apres_kwh", 0) * IDC_CONVERSION_ELECTRICITE_PAC_APRES_MJ_KWH,
                data_site.get("idc_agent_energetique_ef_electricite_pac_apres_somme_mj", 0) / IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_APRES,
            ],
            "Facteur pondération": [
                IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_APRES,
                IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_APRES,
            ],
            "Énergie pondérée (MJ)": [
                data_site.get("idc_agent_energetique_ef_electricite_pac_apres_kwh", 0) * IDC_CONVERSION_ELECTRICITE_PAC_APRES_MJ_KWH * IDC_FACTEUR_PONDERATION_ELECTRICITE_PAC_APRES,
                data_site.get("idc_agent_energetique_ef_electricite_pac_apres_somme_mj", 0),
            ]
        }
    )

    df_agent_energetique_idc_electricite_directe = pd.DataFrame(
        {
            "Agent énergétique": [
                "Electricité (directe) (kWh)",
                "Total Electricité (directe) (MJ)"
            ],
            "Quantité renseignée": [
                str(data_site.get("idc_agent_energetique_ef_electricite_directe_kwh", 0)),
                "-"
            ],
            "Unité": [
                "kWh",
                "MJ"
            ],
            "Facteur conversion MJ": [
                str(IDC_CONVERSION_ELECTRICITE_DIRECTE_MJ_KWH),
                "-"
            ],
            "Énergie (MJ)": [
                data_site.get("idc_agent_energetique_ef_electricite_directe_kwh", 0) * IDC_CONVERSION_ELECTRICITE_DIRECTE_MJ_KWH,
                data_site.get("idc_agent_energetique_ef_electricite_directe_somme_mj", 0) / IDC_FACTEUR_PONDERATION_ELECTRICITE_DIRECTE,
            ],
            "Facteur pondération": [
                IDC_FACTEUR_PONDERATION_ELECTRICITE_DIRECTE,
                IDC_FACTEUR_PONDERATION_ELECTRICITE_DIRECTE,
            ],
            "Énergie pondérée (MJ)": [
                data_site.get("idc_agent_energetique_ef_electricite_directe_kwh", 0) * IDC_CONVERSION_ELECTRICITE_DIRECTE_MJ_KWH * IDC_FACTEUR_PONDERATION_ELECTRICITE_DIRECTE,
                data_site.get("idc_agent_energetique_ef_electricite_directe_somme_mj", 0),
            ]
        }
    )

    df_agent_energetique_idc_autre = pd.DataFrame(
        {
            "Agent énergétique": [
                "Autre (kWh)",
                "Total Autre (MJ)"
            ],
            "Quantité renseignée": [
                str(data_site.get("idc_agent_energetique_ef_autre_kwh", 0)),
                "-"
            ],
            "Unité": [
                "kWh",
                "MJ"
            ],
            "Facteur conversion MJ": [
                str(IDC_CONVERSION_AUTRE_MJ_KWH),
                "-"
            ],
            "Énergie (MJ)": [
                data_site.get("idc_agent_energetique_ef_autre_kwh", 0) * IDC_CONVERSION_AUTRE_MJ_KWH,
                data_site.get("idc_agent_energetique_ef_autre_somme_mj", 0) / IDC_FACTEUR_PONDERATION_AUTRE,
            ],
            "Facteur pondération": [
                IDC_FACTEUR_PONDERATION_AUTRE,
                IDC_FACTEUR_PONDERATION_AUTRE,
            ],
            "Énergie pondérée (MJ)": [
                data_site.get("idc_agent_energetique_ef_autre_kwh", 0) * IDC_CONVERSION_AUTRE_MJ_KWH * IDC_FACTEUR_PONDERATION_AUTRE,
                data_site.get("idc_agent_energetique_ef_autre_somme_mj", 0),
            ]
        }
    )

    return (
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