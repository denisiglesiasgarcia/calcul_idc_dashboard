import streamlit as st
import numpy as np
from typing import List, Dict

# Define energy agent options
OPTIONS_AGENT_ENERGETIQUE_IDC = [
    {
        "label": "CAD réparti (kWh)",
        "unit": "kWh",
        "variable": "agent_energetique_ef_cad_reparti_kwh",
    },
    {
        "label": "CAD tarifé (kWh)",
        "unit": "kWh",
        "variable": "agent_energetique_ef_cad_tarife_kwh",
    },
    {
        "label": "Electricité PAC DD avant 5.8.10 (kWh)",
        "unit": "kWh",
        "variable": "agent_energetique_ef_electricite_pac_avant_kwh",
    },
    {
        "label": "Electricité PAC DD après 5.8.10 (kWh)",
        "unit": "kWh",
        "variable": "agent_energetique_ef_electricite_pac_apres_kwh",
    },
    {
        "label": "Electricité directe (kWh)",
        "unit": "kWh",
        "variable": "agent_energetique_ef_electricite_directe_kwh",
    },
    {
        "label": "Gaz naturel (m³)",
        "unit": "m³",
        "variable": "agent_energetique_ef_gaz_naturel_m3",
    },
    {
        "label": "Gaz naturel (kWh)",
        "unit": "kWh",
        "variable": "agent_energetique_ef_gaz_naturel_kwh",
    },
    {
        "label": "Mazout (litres)",
        "unit": "litres",
        "variable": "agent_energetique_ef_mazout_litres",
    },
    {
        "label": "Mazout (kg)",
        "unit": "kg",
        "variable": "agent_energetique_ef_mazout_kg",
    },
    {
        "label": "Mazout (kWh)",
        "unit": "kWh",
        "variable": "agent_energetique_ef_mazout_kwh",
    },
    {
        "label": "Bois buches dur (stère)",
        "unit": "stère",
        "variable": "agent_energetique_ef_bois_buches_dur_stere",
    },
    {
        "label": "Bois buches tendre (stère)",
        "unit": "stère",
        "variable": "agent_energetique_ef_bois_buches_tendre_stere",
    },
    {
        "label": "Bois buches tendre (kWh)",
        "unit": "kWh",
        "variable": "agent_energetique_ef_bois_buches_tendre_kwh",
    },
    {
        "label": "Pellets (m³)",
        "unit": "m³",
        "variable": "agent_energetique_ef_pellets_m3",
    },
    {
        "label": "Pellets (kg)",
        "unit": "kg",
        "variable": "agent_energetique_ef_pellets_kg",
    },
    {
        "label": "Pellets (kWh)",
        "unit": "kWh",
        "variable": "agent_energetique_ef_pellets_kwh",
    },
    {
        "label": "Plaquettes (m³)",
        "unit": "m³",
        "variable": "agent_energetique_ef_plaquettes_m3",
    },
    {
        "label": "Plaquettes (kWh)",
        "unit": "kWh",
        "variable": "agent_energetique_ef_plaquettes_kwh",
    },
    {
        "label": "Autre (kWh)",
        "unit": "kWh",
        "variable": "agent_energetique_ef_autre_kwh",
    },
]


def validate_agent_energetique_input(label: str, value: str, unit: str) -> float:
    """
    Validate and convert the input value for an energy agent.

    Args:
    label (str): The label of the energy agent.
    value (str): The input value to validate.
    unit (str): The unit of measurement.

    Returns:
    float: The validated and converted value, or 0 if invalid.
    """
    if value is None or value == "":
        st.error(f"{label} doit être un chiffre")
        return 0

    try:
        if isinstance(value, (int, float, np.float64)):
            value = float(value)
        else:
            value = float(str(value).replace(",", ".", 1))

        if value > 0:
            st.text(f"{label}: {value} {unit}")
            return value
        else:
            st.error(f"{label} doit être un chiffre positif")
            return 0
    except ValueError:
        st.error(f"{label} doit être un chiffre")
        return 0

def update_data(
    data: Dict, selected_agents: List[str], options: List[Dict]
) -> Dict:
    """
    Update the data dictionary with energy agent values, setting unselected agents to 0.

    Args:
    data (Dict): The dictionary to update.
    selected_agents (List[str]): The list of currently selected energy agents.
    options (List[Dict]): The list of energy agent options.

    Returns:
    Dict: The updated data dictionary.
    """
    for option in options:
        # Set unselected agents to 0
        if option["label"] not in selected_agents:
            data[option["variable"]] = 0
        # Update the values for selected agents
        else:
            data[option["variable"]] = option.get("value", 0)
    return data


def calculate_total_energy(data: Dict) -> float:
    """
    Calculate the total energy from all energy agents.

    Args:
    data (Dict): The dictionary containing energy agent values.

    Returns:
    float: The total energy sum.
    """
    return sum(
        float(data[option["variable"]]) for option in OPTIONS_AGENT_ENERGETIQUE_IDC
    )


def display_agents_energetiques_idc(
    data: Dict,
):
    """
    Display energy agents inputs and handle user interactions.

    Args:
    data (Dict): The current site data.
    datas_db (Dict): The database containing energy agent values.
    """
    st.markdown(
        '<span style="font-size:1.2em;">**Agents énergétiques utilisés**</span>',
        unsafe_allow_html=True,
    )

    # Get selected energy agents
    selected_agents = []

    # Display multiselect for energy agents
    selected_agents = st.multiselect(
        "Agent(s) énergétique(s):",
        [option["label"] for option in OPTIONS_AGENT_ENERGETIQUE_IDC],
        default=selected_agents,
    )

    # Display input fields for selected agents
    for option in OPTIONS_AGENT_ENERGETIQUE_IDC:
        if option["label"] in selected_agents:
            default_value = get_default_value(data, option)
            value = st.text_input(option["label"] + ":", value=default_value)
            if value != "0":
                option["value"] = validate_agent_energetique_input(
                    option["label"], value, option["unit"]
                )

    # Update data with new values, setting unselected agents to 0
    data = update_data(
        data, selected_agents, OPTIONS_AGENT_ENERGETIQUE_IDC
    )

    # Calculate and display total energy
    total_energy = calculate_total_energy(data)
    if total_energy <= 0:
        st.warning(
            f"Veuillez renseigner une quantité d'énergie utilisée sur la période ({total_energy})"
        )


def get_default_value(data: Dict, option: Dict) -> float:
    """
    Get the default value for an energy agent input field.

    Args:
    data (Dict): The current site data.
    option (Dict): The energy agent option.

    Returns:
    float: The default value for the input field.
    """
    return 0.0
