# sections/helpers/dates.py

import streamlit as st
import pandas as pd
import datetime

def display_dates_periode():
    # Create two columns for the start and end date inputs
    periode_tab_col1, periode_tab_col2 = st.columns(2)

    # Start date input
    with periode_tab_col1:
        # Calculate the date one year before the latest available meteo data
        last_year = pd.to_datetime(
            st.session_state["df_meteo_tre200d0"]["time"].max()
        ) - pd.DateOffset(days=365)
        # Create a date input widget for the start date
        periode_start = st.date_input(
            "Début de la période",
            datetime.date(last_year.year, last_year.month, last_year.day),
        )

    # End date input
    with periode_tab_col2:
        # Get the latest available meteo data date as a string
        max_date_texte = (
            st.session_state["df_meteo_tre200d0"]["time"].max().strftime("%Y-%m-%d")
        )
        # Create a label for the end date input widget
        fin_periode_txt = f"Fin de la période (météo disponible jusqu'au: {max_date_texte})"
        # Get the latest available meteo data date as a datetime object
        max_date = pd.to_datetime(st.session_state["df_meteo_tre200d0"]["time"].max())
        # Create a date input widget for the end date
        periode_end = st.date_input(
            fin_periode_txt,
            datetime.date(max_date.year, max_date.month, max_date.day),
        )

    # Calculate the number of days in the selected period
    periode_nb_jours = (periode_end - periode_start).days + 1

    # Store the calculated period data in the session state
    st.session_state["data"]["periode_nb_jours"] = float(periode_nb_jours)
    st.session_state["data"]["periode_start"] = pd.to_datetime(periode_start)
    st.session_state["data"]["periode_end"] = pd.to_datetime(periode_end)

