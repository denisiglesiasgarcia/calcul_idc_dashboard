# sections/helpers/note_calcul/remarques_idc.py

import streamlit as st

def remarques_note_calcul_idc():
    st.subheader("Remarques concernant tableau Excel OCEN pour le calcul d'IDC", divider="rainbow")
    st.markdown("### Sources")
    st.write(
        "Ce calculateur utilise la 'Directive relative au calcul de l'indice de dépense de chaleur' du 11 novembre 2021.\
        Le tableau Excel officiel pour le calcul de l'Indice de Dépense de Chaleur (IDC) est disponible \
        sur le [site de l'OCEN](https://www.ge.ch/document/energie-idc-form-calcul-indice-depense-chaleur).\
        "
    )
    st.markdown("### Différences entre le tableau Excel OCEN et ce calculateur")
    st.markdown("Il existe certaines différences entre le tableau Excel OCEN et ce calculateur qui sont détaillées ici.\
        Les différences devraient être inférieures à 5%.\
        ")  
    st.markdown(
        "TopoIDC, la plateforme ou l'on déclare les IDC n'est pas open source et il ne m'est pas possible\
        de déterminer les différences.\
        ")
    st.markdown("#### Besoins ECS en énergie finale")
    st.markdown(
        "La première différence est au niveau du besoin théorique ECS en énergie finale $E_{WW}$ (cas d'un comptage de l'ECS inclus dans le relevé), le tableau Excel OCEN va utiliser la formule suivante de la directive:")
    st.latex(r'E_{WW} = \frac{Q_{WW}}{0,90 \cdot 0,65}')
    st.markdown("avec les données de la SIA 380/1 pour $Q_{WW}$. Ce calculateur va utiliser le tableau de la directive ci-dessous. Les différences\
        sont minimes de l'ordre de 128.2 au lieu de 128 pour le cas de l'habitat collectif."
    )

    st.markdown("""
    | Catégorie d'ouvrage | Besoin d'énergie pour l'eau chaude sanitaire Eww [MJ/(m²a)] |
    |---------------------|---------------------------------------------------------------|
    | Habitat collectif   | 128                                                           |
    | Habitat individuel  | 85                                                            |
    | Administration      | 43                                                            |
    | Écoles              | 43                                                            |
    | Commerces           | 43                                                            |
    | Restauration        | 342                                                           |
    | Lieux de rassemblement | 86                                                         |
    | Hôpitaux            | 171                                                           |
    | Industrie           | 43                                                            |
    | Dépôts              | 9                                                             |
    | Installations sportives | 513                                                       |
    | Piscines couvertes  | 513                                                           |
    """)
    st.markdown("#### DJ de référence")
    st.markdown(
        "\
        La directive (équation 2) indique que le calcul des degrés-jour de référence\
        est réalisé en utilisant les valeurs météo du Cahier Technique SIA 2028 pour Genève-Cointrin\
        (le tableau se trouve ci-dessous).\
        ")
    st.markdown("""
    | Janvier | Février | Mars | Avril | Mai | Juin | Juillet | Août | Septembre | Octobre | Novembre | Décembre |
    |---------|---------|------|-------|-----|------|---------|------|-----------|---------|----------|----------|
    |1.7 | 2.9 | 6.5 | 9.4 | 14.4 | 17.6 | 20.2 | 20.0 | 15.4 | 11.2 | 5.6 | 3.1 |
    """)
    st.markdown(
         "Il faut réaliser une interpollation linéaire de ces valeurs, avec comme\
        température de référence intérieure 20°C (logement collectif)\
        et la température de non-chauffage 16°C. C'est donc des DJ20/16.\
        ")
    
    st.markdown("Le tableau Excel OCEN utilise la valeur $3258.311$,\
        ce calculateur utilise la valeur $3260.539$ utilisée dans le programme AMOén.\
        ")

    st.markdown("#### Météo")
    st.markdown(
        "Ce calculateur utilise les données météo de MétéoSuisse pour la station Genève Cointrin, la mesure est tre200d0.\
        Tre200d0 correspond à la moyenne journalière de la température de l'air à 2m du sol.\
        ")
    st.markdown(
        "La source des données météo du tableau Excel OCEN n'est pas connue. C'est bien\
        indiqué que ça provient de MétéoSuisse station Cointrin mais pas la mesure exacte.\
        La différence est de l'ordre de 0.09\% sur toute l'année 2024 entre les 2 mesures.\
        ")