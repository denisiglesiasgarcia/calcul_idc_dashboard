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
        "Variable/Formule",
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
            "Variable/Formule": "periode_nb_jours",
        }
    )

    # C117 → Variante calcul ECS avec/sans comptage séparé
    df_list.append(
        {
            "Dénomination": "Variante calcul ECS avec/sans comptage séparé",
            "Valeur": data_site["comptage_ecs_inclus"],
            "Unité": "",
            "Variante ECS": "Toutes",
            "Commentaire": "Variante calcul ECS avec/sans comptage séparé. True si comptage inclus, False sinon",
            "Excel": "C117",
            "Variable/Formule": "comptage_ecs_inclus",
        }
    )

    # Variante comptage_ecs_inclus True
    
    # C118 → IDC_Bww → Energie finale pour l'ECS
    df_list.append(
        {
            "Dénomination": "IDC_Bww",
            "Valeur": data_site["idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj"],
            "Unité": "MJ",
            "Variante ECS": "Pas de comptage ECS séparé",
            "Commentaire": "Energie finale pour l'ECS",
            "Excel": "C118",
            "Variable/Formule": "idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj",
        }
    )
    # C119 → IDC_Eww → Part d'énergie finale pour ECS
    df_list.append(
        {
            "Dénomination": "IDC_Eww",
            "Valeur": data_site["idc_eww_part_energie_finale_ecs_comptage_ecs_inclus_mj_m2"],
            "Unité": "MJ/m²",
            "Variante ECS": "Pas de comptage ECS séparé",
            "Commentaire": "Part d'énergie finale pour ECS",
            "Excel": "C119",
            "Variable/Formule": "idc_eww_part_energie_finale_ecs_comptage_ecs_inclus_mj_m2",
        }
    )
    # C120 → IDC_Bh → Part chauffage de l'énergie finale




    return pd.DataFrame(df_list, columns=columns)
