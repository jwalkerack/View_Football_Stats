
import streamlit as st
import pandas as pd
import plotly.express as px
from utils import run_query, get_team_filters

def attendance_analysis():
    st.subheader("📊 Attendance Analysis")

    # Fetch team filters from Snowflake
    team_data = get_team_filters()
    countries = team_data["COUNTRY_NAME"].unique()

    # Country Selector
    selected_country = st.selectbox("🌍 Select Country", options=["All"] + list(countries), index=0)

    # Filter leagues based on selected country
    leagues = team_data["LEAGUE_NAME"].unique() if selected_country == "All" else team_data[
        team_data["COUNTRY_NAME"] == selected_country]["LEAGUE_NAME"].unique()
    selected_league = st.selectbox("🏆 Select League", options=["All"] + list(leagues), index=0)

    # Filter teams based on selected country and league
    available_teams = team_data["TEAM_NAME"].unique() if selected_league == "All" else team_data[
        (team_data["COUNTRY_NAME"] == selected_country) & (team_data["LEAGUE_NAME"] == selected_league)]["TEAM_NAME"].unique()

    # Initialize session state for tracking teams
    if "selected_teams" not in st.session_state:
        st.session_state.selected_teams = {}

    # Team Selection
    new_team = st.selectbox(
        "🏟️ Select a Team to Add",
        options=["Select"] + list(available_teams),
        key="temp_team_selector"
    )

    # Add Team Button
    if st.button("➕ Add Team"):
        if new_team != "Select" and new_team not in st.session_state.selected_teams:
            st.session_state.selected_teams[new_team] = True  # Store team in session state

    # Display Confirmed Teams with Remove Buttons
    if st.session_state.selected_teams:
        st.markdown("### ✅ Confirmed Teams:")
        for team in list(st.session_state.selected_teams.keys()):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"🏟️ {team}")
            with col2:
                if st.button(f"🗑 Remove {team}", key=f"remove_{team}"):
                    del st.session_state.selected_teams[team]

    # Confirm Team Button (Optional, acts as a safeguard)
    if st.button("✅ Confirm Selected Teams"):
        if not st.session_state.selected_teams:
            st.warning("⚠️ Please add at least one team before confirming.")

    # Process Button
    if st.button("📈 Process Attendance"):
        if not st.session_state.selected_teams:
            st.warning("⚠️ Please confirm at least one team.")
            return

        # Convert selected team names to team IDs
        team_ids_query = f"""
        SELECT TEAM_ID, TEAM_NAME FROM DIM_TEAMS_V2
        WHERE TEAM_NAME IN ({", ".join([f"'{team}'" for team in st.session_state.selected_teams.keys()])})
        """
        team_id_mapping = run_query(team_ids_query)

        if team_id_mapping.empty:
            st.warning("❌ No matching team IDs found.")
            return

        # Convert team names to a list of IDs
        team_ids = ", ".join([f"'{row['TEAM_ID']}'" for _, row in team_id_mapping.iterrows()])

        # Updated Query: Join FAC_MATCH with DIM_TEAMS_V2 to get Team Names
        query = f"""
        SELECT fm.PLAYED_ON, dt.TEAM_NAME AS HOME_TEAM, fm.ATTENDANCE
        FROM FAC_MATCH fm
        JOIN DIM_TEAMS_V2 dt ON fm.HOME_TEAM_ID = dt.TEAM_ID
        WHERE fm.HOME_TEAM_ID IN ({team_ids}) AND fm.WAS_GAME_POSTPONED = FALSE
        ORDER BY fm.PLAYED_ON
        """
        attendance_data = run_query(query)

        if attendance_data.empty:
            st.warning("❌ No attendance data found for the selected teams.")
            return

        # Convert PLAYED_ON to datetime
        attendance_data["PLAYED_ON"] = pd.to_datetime(attendance_data["PLAYED_ON"])

        # Plot attendance trends
        fig = px.line(
            attendance_data,
            x="PLAYED_ON",
            y="ATTENDANCE",
            color="HOME_TEAM",
            title="Attendance Over Time",
            labels={"PLAYED_ON": "Date", "ATTENDANCE": "Attendance", "HOME_TEAM": "Team"}
        )
        st.plotly_chart(fig, use_container_width=True)
