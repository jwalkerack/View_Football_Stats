import streamlit as st
import pandas as pd
import plotly.express as px
from utils import run_query
import snowflake.connector
import streamlit as st

def get_snowflake_connection():
    """
    Establishes a connection to Snowflake using Streamlit secrets.
    Returns an active Snowflake connection object.
    """
    try:
        conn = snowflake.connector.connect(
            user=st.secrets["snowflake"]["user"],
            password=st.secrets["snowflake"]["password"],
            account=st.secrets["snowflake"]["account"],
            warehouse=st.secrets["snowflake"]["warehouse"],
            database=st.secrets["snowflake"]["database"],
            schema=st.secrets["snowflake"]["schema"]
        )
        return conn
    except Exception as e:
        st.error(f"❌ Snowflake connection failed: {e}")
        return None


def attendance_analysis():
    st.subheader("📊 Attendance Analysis")

    # Step 1: Fetch leagues
    leagues_query = "SELECT DISTINCT LEAGUE_NAME FROM DIM_LEAGUES ORDER BY LEAGUE_NAME;"
    league_data = run_query(leagues_query)

    if league_data.empty:
        st.warning("⚠ No leagues found.")
        return

    leagues = league_data["LEAGUE_NAME"].tolist()

    # Step 2: User selects a league
    selected_league = st.selectbox("🏆 Select League", options=["Select a League"] + leagues, index=0)

    if selected_league == "Select a League":
        st.warning("⚠ Please select a league to proceed.")
        return

    # Step 3: Fetch teams for the selected league
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    teams_query = "SELECT DISTINCT TEAM_NAME FROM DIM_TEAMS WHERE LEAGUE_NAME = %s ORDER BY TEAM_NAME;"
    cursor.execute(teams_query, (selected_league,))
    team_data = cursor.fetchall()
    available_teams = [row[0] for row in team_data]  # Convert tuples to list

    cursor.close()
    conn.close()

    if not available_teams:
        st.warning("⚠ No teams found for this league.")
        return

    # Step 4: Initialize session state for team selection
    if "selected_teams" not in st.session_state:
        st.session_state.selected_teams = {}

    # Step 5: Team Selection
    new_team = st.selectbox(
        "🏟️ Select a Team to Add",
        options=["Select a Team"] + available_teams,
        key="temp_team_selector"
    )

    # Step 6: Add Team Button
    if st.button("➕ Add Team"):
        if new_team != "Select a Team" and new_team not in st.session_state.selected_teams:
            st.session_state.selected_teams[new_team] = True

    # Step 7: Display Confirmed Teams with Remove Buttons
    if st.session_state.selected_teams:
        st.markdown("### ✅ Confirmed Teams:")
        for team in list(st.session_state.selected_teams.keys()):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"🏟️ {team}")
            with col2:
                if st.button(f"🗑 Remove {team}", key=f"remove_{team}"):
                    del st.session_state.selected_teams[team]

    # Step 8: Confirm Selection
    if st.button("✅ Confirm Selected Teams"):
        if not st.session_state.selected_teams:
            st.warning("⚠ Please add at least one team before confirming.")

    # Step 9: Process Attendance Data
    if st.button("📈 Process Attendance"):
        if not st.session_state.selected_teams:
            st.warning("⚠ Please confirm at least one team.")
            return

        # Convert selected teams into SQL-safe format
        team_names = tuple(st.session_state.selected_teams.keys())

        # If only one team is selected, format tuple correctly
        team_names_sql = f"('{team_names[0]}')" if len(team_names) == 1 else str(team_names)

        # Attendance Query (Safe Parameterized Query)
        attendance_query = f"""
        SELECT PLAYED_ON, TEAM_NAME, ATTENDANCE
        FROM ATTENDeNCE_VIEW
        WHERE TEAM_NAME IN {team_names_sql}
        ORDER BY PLAYED_ON ASC;
        """

        attendance_data = run_query(attendance_query)

        if attendance_data.empty:
            st.warning("❌ No attendance data found for the selected teams.")
            return

        # Convert PLAYED_ON to datetime
        attendance_data["PLAYED_ON"] = pd.to_datetime(attendance_data["PLAYED_ON"])

        # Step 10: Plot attendance trends
        fig = px.line(
            attendance_data,
            x="PLAYED_ON",
            y="ATTENDANCE",
            color="TEAM_NAME",
            title="Attendance Over Time",
            labels={"PLAYED_ON": "Date", "ATTENDANCE": "Attendance", "TEAM_NAME": "Team"}
        )
        st.plotly_chart(fig, use_container_width=True)
