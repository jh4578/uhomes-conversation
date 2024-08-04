# config.py

import streamlit as st

# def get_database_config():
#     # Fetching database configuration from Streamlit secrets
DATABASE_CONFIG = {
    'user': st.secrets["db_config"]["user"],
    'password': st.secrets["db_config"]["password"],
    'host': st.secrets["db_config"]["host"],
    'database': st.secrets["db_config"]["database"],
    'port': st.secrets["db_config"]["port"]
}
    # return DATABASE_CONFIG
