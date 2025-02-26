# /main.py

import os
import datetime
import pandas as pd
import streamlit as st
import matplotlib
import sqlite3

st.subheader("Sélection adresse")

# Debug function to check database connection and table existence
def debug_database(db_path: str = "addresses_egid.db") -> None:
    """
    Debug database connection and check if tables exist.
    Prints information about the database path and tables.
    """
    # Get absolute path
    abs_path = os.path.abspath(db_path)
    
    # Check if file exists
    file_exists = os.path.isfile(abs_path)
    
    # Debug information
    st.write(f"Database path: {abs_path}")
    st.write(f"Database file exists: {file_exists}")
    
    if file_exists:
        # Check file size
        file_size = os.path.getsize(abs_path)
        st.write(f"Database file size: {file_size} bytes")
        
        # Try to connect and check tables
        try:
            conn = sqlite3.connect(abs_path)
            cursor = conn.cursor()
            
            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            st.write(f"Tables in database: {[table[0] for table in tables]}")
            
            # Check if addresses table exists and show its structure
            if ('addresses',) in tables:
                cursor.execute("PRAGMA table_info(addresses);")
                columns = cursor.fetchall()
                st.write(f"Columns in addresses table: {columns}")
                
                # Count rows
                cursor.execute("SELECT COUNT(*) FROM addresses;")
                row_count = cursor.fetchone()[0]
                st.write(f"Number of rows in addresses table: {row_count}")
            
            conn.close()
        except Exception as e:
            st.error(f"Error connecting to database: {e}")
    
    # Check current working directory
    st.write(f"Current working directory: {os.getcwd()}")
    
    # List files in current directory
    st.write(f"Files in current directory: {os.listdir('.')}")

# Modify your get_all_addresses function to use absolute path
@st.cache_data
def get_all_addresses(db_path: str = "addresses_egid.db") -> pd.DataFrame:
    """
    Get all addresses from the database for the dropdown list.
    Results are cached by Streamlit.
    """
    # Use absolute path for better reliability
    abs_path = os.path.abspath(db_path)
    
    # Debug info
    print(f"Connecting to database at: {abs_path}")
    
    conn = sqlite3.connect(abs_path)
    try:
        query = "SELECT address, egid FROM addresses ORDER BY address"
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"Error in get_all_addresses: {e}")
        # Return empty DataFrame if there's an error
        return pd.DataFrame(columns=["address", "egid"])
    finally:
        conn.close()

# Add this to your Streamlit app to debug database connection
st.subheader("Database Debug Information")
if st.button("Debug Database Connection"):
    debug_database()

# Get all addresses from the database
df = get_all_addresses()

# Display the dropdown list
address = st.selectbox("Adresse", df["address"].tolist())



st.subheader("Plan de situation")

# TODO: Add a map to show the location of the site

st.subheader("Agents énérgétiques")

# display_agents_energetiques_idc(st.session_state["data"])

# Subheader for the calculation period section
st.subheader("Période de calcul")
