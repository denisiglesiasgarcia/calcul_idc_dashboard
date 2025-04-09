import streamlit as st
from typing import List, Dict, Optional, Tuple
import pandas as pd

# Define data structure
AFFECTATION_OPTIONS = [
    {
        "label": "Habitat collectif (%)",
        "unit": "%",
        "variable": "sre_pourcentage_habitat_collectif",
        "value": 0.0,
    },
    {
        "label": "Habitat individuel (%)",
        "unit": "%",
        "variable": "sre_pourcentage_habitat_individuel",
        "value": 0.0,
    },
    {
        "label": "Administration (%)",
        "unit": "%",
        "variable": "sre_pourcentage_administration",
        "value": 0.0,
    },
    {
        "label": "Écoles (%)",
        "unit": "%",
        "variable": "sre_pourcentage_ecoles",
        "value": 0.0,
    },
    {
        "label": "Commerce (%)",
        "unit": "%",
        "variable": "sre_pourcentage_commerce",
        "value": 0.0,
    },
    {
        "label": "Restauration (%)",
        "unit": "%",
        "variable": "sre_pourcentage_restauration",
        "value": 0.0,
    },
    {
        "label": "Lieux de rassemblement (%)",
        "unit": "%",
        "variable": "sre_pourcentage_lieux_de_rassemblement",
        "value": 0.0,
    },
    {
        "label": "Hôpitaux (%)",
        "unit": "%",
        "variable": "sre_pourcentage_hopitaux",
        "value": 0.0,
    },
    {
        "label": "Industrie (%)",
        "unit": "%",
        "variable": "sre_pourcentage_industrie",
        "value": 0.0,
    },
    {
        "label": "Dépôts (%)",
        "unit": "%",
        "variable": "sre_pourcentage_depots",
        "value": 0.0,
    },
    {
        "label": "Installations sportives (%)",
        "unit": "%",
        "variable": "sre_pourcentage_installations_sportives",
        "value": 0.0,
    },
    {
        "label": "Piscines couvertes (%)",
        "unit": "%",
        "variable": "sre_pourcentage_piscines_couvertes",
        "value": 0.0,
    },
]


class AffectationManager:
    """Class to manage affectation operations."""

    @staticmethod
    def validate_percentage(value: str) -> Tuple[float, bool]:
        """
        Validate if the input is a valid percentage.
        
        Args:
            value: The input value as string
            
        Returns:
            A tuple with the validated float value and a boolean indicating if it's valid
        """
        try:
            float_value = float(value.replace(",", ".", 1))
            return float_value, 0 <= float_value <= 100
        except ValueError:
            return 0.0, False

    @staticmethod
    def get_selected_affectations(data_sites_db: Optional[Dict] = None) -> List[str]:
        """
        Return list of selected affectations based on database values.
        
        Args:
            data_sites_db: Optional database dictionary
            
        Returns:
            List of selected affectation labels
        """
        if not data_sites_db:
            return []
            
        return [
            option["label"]
            for option in AFFECTATION_OPTIONS
            if data_sites_db.get(option["variable"], 0) > 0
        ]

    @staticmethod
    def calculate_affectation_sum() -> float:
        """
        Calculate sum of all affectation percentages.
        Handles case where data_site is a pandas DataFrame.
        
        Returns:
            Sum of all percentages
        """
        total = 0.0
        
        for option in AFFECTATION_OPTIONS:
            variable = option["variable"]
            
            if variable in st.session_state["data_site"]:
                # Handle the case where data_site is a DataFrame (pandas)
                if hasattr(st.session_state["data_site"][variable], 'iloc'):
                    # It's a pandas Series, get the first value
                    value = st.session_state["data_site"][variable].iloc[0] 
                    if not pd.isna(value):  # Check if value is not NaN
                        total += float(value)
                else:
                    # It's a scalar value
                    total += float(st.session_state["data_site"][variable])
                    
        return total

    @staticmethod
    def set_default_affectations(data_sites_db: Optional[Dict] = None) -> None:
        """
        Set default affectation values in session state ONLY for options that
        haven't been manually selected by the user.
        Handles case where data_site is a pandas DataFrame.
        
        Args:
            data_sites_db: Optional database dictionary
        """
        # Get list of options selected by the user (these options already have values set)
        manually_set_options = []
        for option in AFFECTATION_OPTIONS:
            variable = option["variable"]
            
            # Check if the variable exists in data_site and has a positive value
            if variable in st.session_state["data_site"]:
                # Handle the case where data_site is a DataFrame (pandas)
                if hasattr(st.session_state["data_site"][variable], 'any'):
                    # It's a pandas Series
                    if (st.session_state["data_site"][variable] > 0).any():
                        manually_set_options.append(option["label"])
                else:
                    # It's a scalar value
                    if st.session_state["data_site"][variable] > 0:
                        manually_set_options.append(option["label"])
                
        # Get options from database (if available)
        db_selected_labels = AffectationManager.get_selected_affectations(data_sites_db) if data_sites_db else []
        
        # Set defaults ONLY for options that weren't manually selected by user
        for option in AFFECTATION_OPTIONS:
            if option["label"] not in manually_set_options:
                if option["label"] in db_selected_labels and data_sites_db:
                    # Option is in database but not manually set - use DB value
                    option["value"] = data_sites_db.get(option["variable"], 0.0)
                    st.session_state["data_site"][option["variable"]] = data_sites_db.get(
                        option["variable"], 0.0
                    )
                else:
                    # Option not in database and not manually set - use 0
                    option["value"] = 0.0
                    st.session_state["data_site"][option["variable"]] = 0.0


class AffectationUI:
    """Class to handle the UI elements for affectations."""
    
    def __init__(self, sre_renovation_m2: float, data_sites_db: Optional[Dict] = None):
        """
        Initialize with required parameters.
        
        Args:
            sre_renovation_m2: Surface renovation in m²
            data_sites_db: Optional database dictionary
        """
        self.sre_renovation_m2 = sre_renovation_m2
        self.data_sites_db = data_sites_db
        self.manager = AffectationManager()
        
    def display_header(self) -> None:
        """Display the section header."""
        st.markdown(
            '<span style="font-size:1.2em;">**Affectations**</span>', 
            unsafe_allow_html=True
        )
        
    def display_multiselect(self) -> List[str]:
        """
        Display the multiselect for affectations.
        
        Returns:
            List of selected affectation labels
        """
        return st.multiselect(
            "Affectation(s):",
            [option["label"] for option in AFFECTATION_OPTIONS],
            default=self.manager.get_selected_affectations(self.data_sites_db),
        )
        
    def display_input_fields(self, selected_affectations: List[str]) -> None:
        """
        Display input fields for selected affectations.
        
        Args:
            selected_affectations: List of selected affectation labels
        """
        for option in AFFECTATION_OPTIONS:
            if option["label"] in selected_affectations:
                default_value = (
                    self.data_sites_db.get(option["variable"], 0.0) 
                    if self.data_sites_db else 0.0
                )
                
                value = st.text_input(
                    option["label"] + ":",
                    value=default_value,
                )
                
                if value != "0":
                    float_value, is_valid = self.manager.validate_percentage(value)
                    
                    if is_valid:
                        st.text(
                            f"{option['label']} {float_value} {option['unit']} → "
                            f"{round(float_value * float(self.sre_renovation_m2) / 100, 2)} m²"
                        )
                        option["value"] = float_value
                        st.session_state["data_site"][option["variable"]] = float_value
                    else:
                        st.warning("Valeur doit être comprise entre 0 et 100")
                        option["value"] = 0.0
                        st.session_state["data_site"][option["variable"]] = 0.0
                else:
                    option["value"] = 0.0
                    st.session_state["data_site"][option["variable"]] = 0.0
                    
    def display_validation_message(self, total: float) -> None:
        """
        Display validation message for the total percentage.
        
        Args:
            total: Total percentage
        """
        if total != 100:
            st.warning(f"Somme des pourcentages doit être égale à 100% ({total})")


def display_affectations_idc(sre_renovation_m2: float, data_sites_db: Optional[Dict] = None) -> float:
    """
    Main function to display and process affectations.
    
    Args:
        sre_renovation_m2: Surface renovation in m²
        data_sites_db: Optional database dictionary, defaults to None
        
    Returns:
        Total percentage sum
    """
    # Initialize the UI
    ui = AffectationUI(sre_renovation_m2, data_sites_db)
    
    # Display header
    ui.display_header()
    
    # Get default selections from database if available, otherwise empty list
    default_selections = ui.manager.get_selected_affectations(data_sites_db) if data_sites_db else []
    
    # Display multiselect with appropriate defaults
    selected_affectations = st.multiselect(
        "Affectation(s):",
        [option["label"] for option in AFFECTATION_OPTIONS],
        default=default_selections,
    )
    
    # Display input fields for selected options
    # This will update session_state with user input values
    ui.display_input_fields(selected_affectations)
    
    # Set default values for unselected options WITHOUT overriding user inputs
    ui.manager.set_default_affectations(data_sites_db)
    
    # Calculate total percentage
    affectation_sum = ui.manager.calculate_affectation_sum()
    
    # Display validation message
    ui.display_validation_message(affectation_sum)

    return affectation_sum