# /main.py

import os
import datetime
import pandas as pd
import streamlit as st
import matplotlib
import sqlite3

st.subheader("Sélection adresse")




# Modify your get_all_addresses function to use absolute path
@st.cache_data
def get_all_addresses(db_path: str = "adresses_egid.db") -> pd.DataFrame:
    """
    Get all addresses from the database for the dropdown list.
    Results are cached by Streamlit.
    """
    # Use absolute path for better reliability
    abs_path = os.path.abspath(db_path)
    
    # Debug info
    # print(f"Connecting to database at: {abs_path}")
    
    conn = sqlite3.connect(abs_path)
    try:
        query = "SELECT adresse, egid FROM adresses_egid ORDER BY adresse"
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"Error in get_all_addresses: {e}")
        # Return empty DataFrame if there's an error
        return pd.DataFrame(columns=["adresse", "egid"])
    finally:
        conn.close()

# Get all addresses from the database
df = get_all_addresses()

# Create combined options for the multiselect with address and EGID
# First make sure there are no missing values
df_display = df.copy()
df_display.fillna({"egid": "N/A"}, inplace=True)

# Create a combined display string for each address
display_options = [f"{row['adresse']} ({row['egid']})" for _, row in df_display.iterrows()]

# Create a dictionary to map display options back to the original data
options_map = {f"{row['adresse']} ({row['egid']})": {"adresse": row['adresse'], "egid": row['egid']} 
               for _, row in df_display.iterrows()}

# Display the multiselect with combined address and EGID
selected_options = st.multiselect(
    label="Adresse",
    options=display_options,
    default=[],
    placeholder="Select one or more addresses..."
)

# Check if any addresses are selected
if selected_options:
    st.write(f"{len(selected_options)} adresse(s) sélectionnée:")
    
    # Create a list to store selected addresses and EGIDs
    selected_addresses = []
    selected_egids = []
    
    # Extract the selected addresses and EGIDs from the options map
    for option in selected_options:
        selected_addresses.append(options_map[option]["adresse"])
        selected_egids.append(options_map[option]["egid"])
    
    # Create a dataframe of selected items
    selected_data = {
        "adresse": selected_addresses,
        "egid": selected_egids
    }
    selected_df = pd.DataFrame(selected_data)
    
    # Display the selected data
    st.dataframe(selected_df)

else:
    st.warning("Sélectionner au moins une adresse pour continuer.")

st.subheader("Plan de situation")

# TODO: Add a map to show the location of the site

st.subheader("Agents énérgétiques")

# display_agents_energetiques_idc(st.session_state["data"])

# Subheader for the calculation period section
st.subheader("Période de calcul")
