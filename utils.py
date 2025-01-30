# Function to run queries

import streamlit as st
import snowflake.connector
import pandas as pd
@st.cache_data(ttl=600)
def run_query(query):
    # Open a new connection for each query
    conn = snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"]
    )
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
    finally:
        # Ensure the connection is closed properly
        cursor.close()
        conn.close()
    return df

def get_team_filters():
    query = """
    SELECT DISTINCT COUNTRY_NAME, SHORT_NAME AS LEAGUE_NAME, TEAM_NAME 
    FROM DIM_TEAMS_V2
    """
    return run_query(query)


def get_player_stats(selected_country=None, selected_league=None):
    query = """
    SELECT PLAYER_ID, PLAYER_NAME, TEAM_NAME, LEAGUE_NAME, COUNTRY_NAME, 
           T_GAMES_PLAYED, T_STARTER_GAMES, T_MINUTES_PLAYED, 
           T_GOALS, T_ASSISTS, G90, GPG, MPG, 
           T_YELLOW_CARDS, T_RED_CARDS
    FROM VW_PLAYER_STATS
    """

    conditions = []

    if selected_country and selected_country != "Select":
        conditions.append(f"COUNTRY_NAME = '{selected_country}'")

    if selected_league and selected_league != "Select":
        conditions.append(f"SHORT_NAME = '{selected_league}'")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    # Debugging: Log final query


    return run_query(query)
