import streamlit as st
import numpy as np
from typing import List, Dict, Optional, Union, Tuple

# Define energy agent options
OPTIONS_AGENT_ENERGETIQUE_IDC = [
    {
        "label": "CAD réparti (kWh)",
        "unit": "kWh",
        "variable": "idc_agent_energetique_ef_cad_reparti_kwh",
        "value": 0.0,
    },
    {
        "label": "CAD tarifé (kWh)",
        "unit": "kWh",
        "variable": "idc_agent_energetique_ef_cad_tarife_kwh",
        "value": 0.0,
    },
    {
        "label": "Electricité PAC DD avant 5.8.10 (kWh)",
        "unit": "kWh",
        "variable": "idc_agent_energetique_ef_electricite_pac_avant_kwh",
        "value": 0.0,
    },
    {
        "label": "Electricité PAC DD après 5.8.10 (kWh)",
        "unit": "kWh",
        "variable": "idc_agent_energetique_ef_electricite_pac_apres_kwh",
        "value": 0.0,
    },
    {
        "label": "Electricité directe (kWh)",
        "unit": "kWh",
        "variable": "idc_agent_energetique_ef_electricite_directe_kwh",
        "value": 0.0,
    },
    {
        "label": "Gaz naturel (m³)",
        "unit": "m³",
        "variable": "idc_agent_energetique_ef_gaz_naturel_m3",
        "value": 0.0,
    },
    {
        "label": "Gaz naturel (kWh)",
        "unit": "kWh",
        "variable": "idc_agent_energetique_ef_gaz_naturel_kwh",
        "value": 0.0,
    },
    {
        "label": "Mazout (litres)",
        "unit": "litres",
        "variable": "idc_agent_energetique_ef_mazout_litres",
        "value": 0.0,
    },
    {
        "label": "Mazout (kg)",
        "unit": "kg",
        "variable": "idc_agent_energetique_ef_mazout_kg",
        "value": 0.0,
    },
    {
        "label": "Mazout (kWh)",
        "unit": "kWh",
        "variable": "idc_agent_energetique_ef_mazout_kwh",
        "value": 0.0,
    },
    {
        "label": "Bois buches dur (stère)",
        "unit": "stère",
        "variable": "idc_agent_energetique_ef_bois_buches_dur_stere",
        "value": 0.0,
    },
    {
        "label": "Bois buches tendre (stère)",
        "unit": "stère",
        "variable": "idc_agent_energetique_ef_bois_buches_tendre_stere",
        "value": 0.0,
    },
    {
        "label": "Bois buches tendre (kWh)",
        "unit": "kWh",
        "variable": "idc_agent_energetique_ef_bois_buches_tendre_kwh",
        "value": 0.0,
    },
    {
        "label": "Pellets (m³)",
        "unit": "m³",
        "variable": "idc_agent_energetique_ef_pellets_m3",
        "value": 0.0,
    },
    {
        "label": "Pellets (kg)",
        "unit": "kg",
        "variable": "idc_agent_energetique_ef_pellets_kg",
        "value": 0.0,
    },
    {
        "label": "Pellets (kWh)",
        "unit": "kWh",
        "variable": "idc_agent_energetique_ef_pellets_kwh",
        "value": 0.0,
    },
    {
        "label": "Plaquettes (m³)",
        "unit": "m³",
        "variable": "idc_agent_energetique_ef_plaquettes_m3",
        "value": 0.0,
    },
    {
        "label": "Plaquettes (kWh)",
        "unit": "kWh",
        "variable": "idc_agent_energetique_ef_plaquettes_kwh",
        "value": 0.0,
    },
    {
        "label": "Autre (kWh)",
        "unit": "kWh",
        "variable": "idc_agent_energetique_ef_autre_kwh",
        "value": 0.0,
    },
]

OPTIONS_AGENT_ENERGETIQUE_IDC_ECS = [
    {
        "label": "CAD réparti (kWh)",
        "unit": "kWh",
        "variable": "idc_ecs_agent_energetique_ef_cad_reparti_kwh",
        "value": 0.0,
    },
    {
        "label": "CAD tarifé (kWh)",
        "unit": "kWh",
        "variable": "idc_ecs_agent_energetique_ef_cad_tarife_kwh",
        "value": 0.0,
    },
    {
        "label": "Electricité PAC DD avant 5.8.10 (kWh)",
        "unit": "kWh",
        "variable": "idc_ecs_agent_energetique_ef_electricite_pac_avant_kwh",
        "value": 0.0,
    },
    {
        "label": "Electricité PAC DD après 5.8.10 (kWh)",
        "unit": "kWh",
        "variable": "idc_ecs_agent_energetique_ef_electricite_pac_apres_kwh",
        "value": 0.0,
    },
    {
        "label": "Electricité directe (kWh)",
        "unit": "kWh",
        "variable": "idc_ecs_agent_energetique_ef_electricite_directe_kwh",
        "value": 0.0,
    },
    {
        "label": "Gaz naturel (m³)",
        "unit": "m³",
        "variable": "idc_ecs_agent_energetique_ef_gaz_naturel_m3",
        "value": 0.0,
    },
    {
        "label": "Gaz naturel (kWh)",
        "unit": "kWh",
        "variable": "idc_ecs_agent_energetique_ef_gaz_naturel_kwh",
        "value": 0.0,
    },
    {
        "label": "Mazout (litres)",
        "unit": "litres",
        "variable": "idc_ecs_agent_energetique_ef_mazout_litres",
        "value": 0.0,
    },
    {
        "label": "Mazout (kg)",
        "unit": "kg",
        "variable": "idc_ecs_agent_energetique_ef_mazout_kg",
        "value": 0.0,
    },
    {
        "label": "Mazout (kWh)",
        "unit": "kWh",
        "variable": "idc_ecs_agent_energetique_ef_mazout_kwh",
        "value": 0.0,
    },
    {
        "label": "Bois buches dur (stère)",
        "unit": "stère",
        "variable": "idc_ecs_agent_energetique_ef_bois_buches_dur_stere",
        "value": 0.0,
    },
    {
        "label": "Bois buches tendre (stère)",
        "unit": "stère",
        "variable": "idc_ecs_agent_energetique_ef_bois_buches_tendre_stere",
        "value": 0.0,
    },
    {
        "label": "Bois buches tendre (kWh)",
        "unit": "kWh",
        "variable": "idc_ecs_agent_energetique_ef_bois_buches_tendre_kwh",
        "value": 0.0,
    },
    {
        "label": "Pellets (m³)",
        "unit": "m³",
        "variable": "idc_ecs_agent_energetique_ef_pellets_m3",
        "value": 0.0,
    },
    {
        "label": "Pellets (kg)",
        "unit": "kg",
        "variable": "idc_ecs_agent_energetique_ef_pellets_kg",
        "value": 0.0,
    },
    {
        "label": "Pellets (kWh)",
        "unit": "kWh",
        "variable": "idc_ecs_agent_energetique_ef_pellets_kwh",
        "value": 0.0,
    },
    {
        "label": "Plaquettes (m³)",
        "unit": "m³",
        "variable": "idc_ecs_agent_energetique_ef_plaquettes_m3",
        "value": 0.0,
    },
    {
        "label": "Plaquettes (kWh)",
        "unit": "kWh",
        "variable": "idc_ecs_agent_energetique_ef_plaquettes_kwh",
        "value": 0.0,
    },
    {
        "label": "Autre (kWh)",
        "unit": "kWh",
        "variable": "idc_ecs_agent_energetique_ef_autre_kwh",
        "value": 0.0,
    },
]

class EnergyAgentManager:
    """Class to manage energy agent operations."""
    
    def __init__(self, options_list=OPTIONS_AGENT_ENERGETIQUE_IDC):
        """
        Initialize with the desired options list.
        
        Args:
            options_list: The list of energy agent options to use
        """
        self.options_list = options_list
    
    def validate_input(self, label: str, value: str, unit: str) -> Tuple[float, bool]:
        """
        Validate and convert the input value for an energy agent.

        Args:
            label: The label of the energy agent
            value: The input value to validate
            unit: The unit of measurement

        Returns:
            A tuple with the validated value and a boolean indicating if it's valid
        """
        if not value or value == "":
            return 0.0, False

        try:
            if isinstance(value, (int, float, np.float64)):
                float_value = float(value)
            else:
                float_value = float(str(value).replace(",", ".", 1))

            return float_value, float_value > 0
        except ValueError:
            return 0.0, False

    def get_selected_agents(self, data: Dict) -> List[str]:
        """
        Determine which agents were previously selected based on non-zero values.

        Args:
            data: The dictionary containing energy agent values

        Returns:
            List of previously selected agent labels
        """
        selected = []
        for option in self.options_list:
            if option["variable"] in data:
                value = data[option["variable"]]
                
                # Check if value is a pandas Series
                if hasattr(value, 'any'):  # Pandas Series have this method
                    # Use the first value if it's a Series and not empty
                    if not value.empty:
                        try:
                            # Extract the first value and check if it's positive
                            float_val = float(value.iloc[0])
                            if float_val > 0:
                                selected.append(option["label"])
                        except (ValueError, TypeError):
                            pass  # Skip if conversion fails
                elif value is not None:  # For non-Series values
                    try:
                        float_val = float(value)
                        if float_val > 0:
                            selected.append(option["label"])
                    except (ValueError, TypeError):
                        pass  # Skip if conversion fails
        return selected

    def update_data(self, data: Dict, selected_agents: List[str], agent_values: Dict[str, float]) -> Dict:
        """
        Update the data dictionary with energy agent values, setting unselected agents to 0.

        Args:
            data: The dictionary to update
            selected_agents: The list of currently selected energy agents
            agent_values: Dictionary mapping variable names to their values

        Returns:
            The updated data dictionary
        """
        updated_data = data.copy()
        
        # First set all agent values to 0
        for option in self.options_list:
            updated_data[option["variable"]] = 0
        
        # Then update only the selected ones with their values
        for variable, value in agent_values.items():
            updated_data[variable] = value
        
        return updated_data

    def calculate_total_energy(self, data: Dict) -> float:
        """
        Calculate the total energy from all energy agents.

        Args:
            data: The dictionary containing energy agent values

        Returns:
            The total energy sum
        """
        total = 0.0
        for option in self.options_list:
            if option["variable"] in data:
                value = data[option["variable"]]
                # Check if value is a pandas Series
                if hasattr(value, 'any'):  # Pandas Series have this method
                    # Use the first value if it's a Series
                    if not value.empty:
                        try:
                            total += float(value.iloc[0])
                        except (ValueError, TypeError):
                            pass  # Skip if conversion fails
                elif value is not None:  # For non-Series values
                    try:
                        float_val = float(value)
                        total += float_val
                    except (ValueError, TypeError):
                        pass  # Skip if conversion fails
        return total

    def get_default_value(self, data: Dict, variable: str) -> Union[float, str]:
        """
        Get the default value for an energy agent input field.

        Args:
            data: The current site data
            variable: The variable name to look up

        Returns:
            The default value for the input field
        """
        if variable in data:
            value = data[variable]
            
            # Check if value is a pandas Series
            if hasattr(value, 'any'):  # Pandas Series have this method
                # Use the first value if it's a Series and not empty
                if not value.empty:
                    try:
                        # Extract the first value and check if it's positive
                        float_val = float(value.iloc[0])
                        if float_val > 0:
                            return str(float_val)
                    except (ValueError, TypeError):
                        pass  # Skip if conversion fails
            elif value is not None:  # For non-Series values
                try:
                    float_val = float(value)
                    # Only return non-zero values
                    if float_val > 0:
                        return str(float_val)
                except (ValueError, TypeError):
                    pass  # Skip if conversion fails
        return ""

    def set_default_values(self, data: Dict, data_db: Optional[Dict] = None) -> None:
        """
        Set default values in the data dictionary for all options.
        Preserves any existing values.

        Args:
            data: The data dictionary to update
            data_db: Optional database values to use as defaults
        """
        for option in self.options_list:
            variable = option["variable"]
            
            # Skip if the variable is already set in the data
            if variable in data and data[variable] != 0:
                continue
                
            # Use database value if available
            if data_db and variable in data_db and data_db[variable] != 0:
                data[variable] = data_db[variable]
            else:
                # Otherwise set to 0
                data[variable] = 0


class EnergyAgentUI:
    """Class to handle the UI elements for energy agents."""
    
    def __init__(self, data: Dict, data_db: Optional[Dict] = None, options_list=None, title=None):
        """
        Initialize with required parameters.
        
        Args:
            data: The current site data
            data_db: Optional database dictionary with default values
            options_list: Optional list of energy agent options
            title: Optional title for the section
        """
        self.data = data
        self.data_db = data_db
        self.options_list = options_list if options_list is not None else OPTIONS_AGENT_ENERGETIQUE_IDC
        self.title = title if title is not None else "Agents énergétiques utilisés"
        self.manager = EnergyAgentManager(self.options_list)
        self.agent_values = {}  # To store validated input values
        
    def display_header(self) -> None:
        """Display the section header."""
        st.markdown(
            f'<span style="font-size:1.2em;">**{self.title}**</span>',
            unsafe_allow_html=True,
        )
        
    def display_multiselect(self, is_ecs=False) -> List[str]:
        """
        Display the multiselect for energy agents.
        
        Args:
            is_ecs: Whether this is for ECS agents or not
            
        Returns:
            List of selected energy agent labels
        """
        default_selected = self.manager.get_selected_agents(self.data)
        
        # Create a unique key for the multiselect
        multiselect_key = "energy_agents_ecs_multiselect" if is_ecs else "energy_agents_idc_multiselect"
        
        return st.multiselect(
            "Agent(s) énergétique(s):",
            [option["label"] for option in self.options_list],
            default=default_selected,
            key=multiselect_key
        )
        
    def display_input_fields(self, selected_agents: List[str], key_prefix: str = "") -> Dict[str, float]:
        """
        Display input fields for selected energy agents.
        
        Args:
            selected_agents: List of selected energy agent labels
            key_prefix: Prefix to add to input keys for uniqueness
            
        Returns:
            Dictionary mapping variable names to validated values
        """
        result_values = {}
        
        for option in self.options_list:
            if option["label"] in selected_agents:
                default_value = self.manager.get_default_value(self.data, option["variable"])
                
                # Create a unique key for each input to avoid Streamlit widget conflicts
                input_key = f"{key_prefix}energy_agent_{option['variable']}"
                
                value = st.text_input(
                    option["label"] + ":",
                    value=default_value,
                    key=input_key
                )
                
                if value:
                    float_value, is_valid = self.manager.validate_input(
                        option["label"], value, option["unit"]
                    )
                    
                    if is_valid:
                        st.text(f"{option['label']}: {float_value} {option['unit']}")
                        option["value"] = float_value
                        result_values[option["variable"]] = float_value
                    else:
                        st.error(f"{option['label']} doit être un chiffre positif")
                        option["value"] = 0.0
                        result_values[option["variable"]] = 0.0
        
        return result_values
                    
    def display_total_energy(self, total: float) -> None:
        """
        Display the total energy and validation message.
        
        Args:
            total: The total energy value
        """
        if total <= 0:
            st.warning(
                f"Veuillez renseigner une quantité d'énergie utilisée sur la période ({total})"
            )
        else:
            st.success(f"Total énergie: {total:.2f} kWh")


def display_agents_energetiques_idc(data: Dict, data_db: Optional[Dict] = None, is_ecs: bool = False, title: Optional[str] = None) -> float:
    """
    Main function to display and process energy agents.
    Returns the total energy in MJ for energy assessment calculations.

    Args:
        data: The current site data
        data_db: Optional database dictionary with default values
        is_ecs: If True, use the ECS options list; otherwise use the IDC options list
        title: Optional custom title for the section

    Returns:
        The total energy in MJ
    """
    # Choose the appropriate options list
    options_list = OPTIONS_AGENT_ENERGETIQUE_IDC_ECS if is_ecs else OPTIONS_AGENT_ENERGETIQUE_IDC
    
    # Set the default title if none is provided
    if title is None:
        title = "Agents énergétiques ECS" if is_ecs else "Agents énergétiques utilisés"
    
    # Initialize the UI with the appropriate options list and title
    ui = EnergyAgentUI(data, data_db, options_list=options_list, title=title)
    
    # Display header
    ui.display_header()
    
    # Display multiselect with appropriate defaults
    selected_agents = ui.display_multiselect(is_ecs=is_ecs)
    
    # Make input keys unique by adding a prefix
    input_key_prefix = "ecs_" if is_ecs else "idc_"
    
    # Display input fields for selected options and get validated values
    agent_values = ui.display_input_fields(selected_agents, key_prefix=input_key_prefix)
    
    # Update data with new values, setting unselected agents to 0
    updated_data = ui.manager.update_data(data, selected_agents, agent_values)
    
    # Update the original data dictionary
    for key, value in updated_data.items():
        data[key] = value
    
    # Calculate and display total energy
    total_energy = ui.manager.calculate_total_energy(data)
    ui.display_total_energy(total_energy)
    
    # Convert total energy to MJ for energy assessment (1 kWh = 3.6 MJ)
    total_energy_mj = total_energy * 3.6
    
    return total_energy_mj