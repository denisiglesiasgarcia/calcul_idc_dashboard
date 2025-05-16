# sections\helpers\resultats_idc.py

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

def show_results_idc(data_site):
    try:
        if ("idc_sre_m2" in data_site and \
            "somme_pourcentage_affectations" in data_site and
            "idc_somme_agents_energetiques_mj" in data_site and
            "idc_resultat_comptage_ecs_inclus_mj_m2" in data_site and
            data_site["idc_sre_m2"] > 0 and
            data_site["somme_pourcentage_affectations"] == 100 and
            data_site["idc_somme_agents_energetiques_mj"] >= 0 and
            isinstance(data_site["idc_resultat_comptage_ecs_inclus_mj_m2"], (float, int))
        ):
            if data_site["comptage_ecs_inclus"]:
                idc_value = data_site['idc_resultat_comptage_ecs_inclus_mj_m2']
            elif not data_site["comptage_ecs_inclus"]:
                idc_value = data_site['idc_resultat_comptage_ecs_non_inclus_mj_m2']
            
            st.markdown("##### Valeur de l'IDC")
            # Display text results
            col1, col2 = st.columns([1, 1])
            
            # Create bar chart showing the IDC result compared to reference values
            with col1:
                            
                # Define IDC thresholds
                thresholds = [150, 250, 350, 450, 550]
                threshold_labels = ["Très bon", "Bon", "Moyen", "Élevé", "Très élevé"]
                # Compare IDC value to thresholds and determine category
                for i, threshold in enumerate(thresholds):
                    if idc_value <= threshold:
                        category = threshold_labels[i]
                        break
                else:
                    category = "Extrêmement élevé"

                if category == "Extrêmement élevé":
                    text_figure = f"Votre bâtiment a un IDC de **{idc_value:.1f} MJ/m²**, ce qui est considéré comme '**{category}**' car il " + \
                        f"dépasse **{thresholds[-1]} MJ/m²**."
                else:
                    text_figure = f"Votre bâtiment a un IDC de **{idc_value:.1f} MJ/m²**, ce qui est considéré comme '**{category}**' car il " + \
                        f"est inférieur à **{thresholds[i]} MJ/m²**."

                # Create a simple bar chart with the IDC value
                fig = go.Figure()
                
                # Add a bar for the IDC value
                display_value = max(0, idc_value)
                fig.add_trace(go.Bar(
                    x=["Votre bâtiment"],
                    y=[display_value],
                    marker_color='#1a9641',
                    text=[f"{idc_value:.1f} MJ/m²"],
                    textposition='outside',
                ))
                
                # Customize layout
                fig.update_layout(
                    xaxis_title="",
                    yaxis_title="IDC (MJ/m²)",
                    height=400,
                    width=10,
                    margin=dict(l=20, r=20, t=10, b=20),
                )
                
                # Display the chart
                st.plotly_chart(fig, use_container_width=True)
                
                # Warning for negative values
                if idc_value < 0:
                    st.warning(f"Attention: La valeur IDC est négative ({idc_value:.2f} MJ/m²), ce qui indique probablement une erreur dans les données.")
            
            with col2:
                # Résultats de l'IDC
                st.markdown(text_figure)
            
            # Create energy sources breakdown
            st.markdown("##### Répartition des agents énergétiques")
            
            # Extract energy sources and their values
            energy_sources = {
                "CAD réparti": data_site.get("idc_agent_energetique_ef_cad_reparti_somme_mj", 0),
                "CAD tarifé": data_site.get("idc_agent_energetique_ef_cad_tarife_somme_mj", 0),
                "Électricité PAC (avant)": data_site.get("idc_agent_energetique_ef_electricite_pac_avant_somme_mj", 0),
                "Électricité PAC (après)": data_site.get("idc_agent_energetique_ef_electricite_pac_apres_somme_mj", 0),
                "Électricité directe": data_site.get("idc_agent_energetique_ef_electricite_directe_somme_mj", 0),
                "Gaz naturel": data_site.get("idc_agent_energetique_ef_gaz_naturel_somme_mj", 0),
                "Mazout": data_site.get("idc_agent_energetique_ef_mazout_somme_mj", 0),
                "Bois (bûches dur)": data_site.get("idc_agent_energetique_ef_bois_buches_dur_somme_mj", 0),
                "Bois (bûches tendre)": data_site.get("idc_agent_energetique_ef_bois_buches_tendre_somme_mj", 0),
                "Pellets": data_site.get("idc_agent_energetique_ef_pellets_somme_mj", 0),
                "Plaquettes": data_site.get("idc_agent_energetique_ef_plaquettes_somme_mj", 0),
                "Autre": data_site.get("idc_agent_energetique_ef_autre_somme_mj", 0)
            }
            
            # Filter out zero values
            energy_sources = {k: v for k, v in energy_sources.items() if v > 0}
            
            if energy_sources:
                col1, col2 = st.columns([3, 2])
                
                with col1:
                    # Bar chart for energy sources
                    energy_df = {"Source": list(energy_sources.keys()), 
                                "Consommation (MJ)": list(energy_sources.values())}
                    
                    fig_bar = px.bar(
                        energy_df,
                        x="Source",
                        y="Consommation (MJ)",
                        color="Source",
                        title="Consommation par agent énergétique"
                    )
                    
                    fig_bar.update_layout(
                        xaxis_title="",
                        height=400
                    )
                    
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with col2:
                    # Pie chart for energy distribution
                    fig_pie = px.pie(
                        values=list(energy_sources.values()),
                        names=list(energy_sources.keys()),
                        title="Répartition en pourcentage"
                    )
                    
                    fig_pie.update_layout(
                        height=400
                    )
                    
                    st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Aucune donnée sur les agents énergétiques n'est disponible.")
            
            # Add breakdown between heating and domestic hot water
            st.markdown("##### Répartition chauffage et eau chaude sanitaire")
            
            heating_mj = data_site.get("idc_bh_energie_finale_chauffage_comptage_ecs_inclus_mj", 0)
            hotwater_mj = data_site.get("idc_bww_energie_finale_ecs_comptage_ecs_inclus_mj", 0)
            
            # Ensure we handle negative values properly for visualization
            heating_display = max(0, heating_mj)
            hotwater_display = max(0, hotwater_mj)
            
            if heating_mj + hotwater_mj > 0:
                usage_df = {
                    "Usage": ["Chauffage", "Eau chaude sanitaire"],
                    "Consommation (MJ)": [heating_display, hotwater_display]
                }
                
                fig_usage = px.bar(
                    usage_df,
                    x="Usage",
                    y="Consommation (MJ)",
                    color="Usage",
                    color_discrete_sequence=["#FF9E44", "#5BC0EB"],
                    title="Répartition entre chauffage et eau chaude sanitaire"
                )
                
                st.plotly_chart(fig_usage, use_container_width=True)
                
                # Add text explanation if there are negative values
                if heating_mj < 0:
                    st.warning(f"La consommation pour le chauffage présente une valeur négative ({heating_mj:.2f} MJ), " +
                              "ce qui peut indiquer un problème dans les données ou dans le calcul.")
                
        else:
            st.warning("Veuillez renseigner tous les éléments nécessaires pour le calcul de l'IDC.")

    except Exception as e:
        st.error(f"Erreur dans le calcul de l'IDC: {e}")
        import traceback
        st.error(traceback.format_exc())