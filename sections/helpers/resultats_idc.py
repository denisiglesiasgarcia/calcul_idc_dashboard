# sections\helpers\resultats_idc.py

import streamlit as st

# TODO: Bug initialisation idc_resultat_comptage_ecs_inclus_mj_m2
def show_results_idc(data_site):
    try:
        if ("idc_sre_m2" in data_site and \
            "somme_pourcentage_affectations" in data_site and
            "idc_somme_agents_energetiques_mj" in data_site and
            "idc_resultat_comptage_ecs_inclus_mj_m2" in data_site and
            data_site["idc_sre_m2"] > 0 and
            data_site["somme_pourcentage_affectations"] > 0 and
            data_site["idc_somme_agents_energetiques_mj"] > 0 and
            isinstance(data_site["idc_resultat_comptage_ecs_inclus_mj_m2"], (float, int))
        ):
            if data_site["comptage_ecs_inclus"]:
                st.markdown("##### Comptage ECS inclus dans les relevés")
                st.write(f"Valeur de l'IDC calculée: \
                    {st.session_state['data_site']['idc_resultat_comptage_ecs_inclus_mj_m2']:.2f} MJ/m²")
   
            elif not data_site["comptage_ecs_inclus"]:
                st.markdown("##### Comptage ECS non-inclus dans les relevés")
                st.write(f"Valeur de l'IDC calculée: \
                    {st.session_state['data_site']['idc_resultat_comptage_ecs_non_inclus_mj_m2']:.2f} MJ/m²")

        else:
            st.warning("Veuillez renseigner tous les éléments nécessaires pour le calcul de l'IDC.")

    except Exception as e:
        st.error(f"Erreur dans le calcul de l'IDC: {e}")