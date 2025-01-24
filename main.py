import streamlit as st
import pandas as pd
import snowflake.connector
import plotly.express as px


# Function to connect to Snowflake
@st.cache_resource
def get_snowflake_connection():
    return snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"]
    )


# Function to run queries
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


# Fetch unique leagues and teams
def get_unique_leagues_and_teams():
    query = """
    SELECT DISTINCT LEAGUE_NAME, HOME_TEAM_NAME
    FROM TEAM_SUMMARY
    """
    return run_query(query)


# Fetch attendance data for selected teams
def get_attendance_data(teams):
    query = f"""
    SELECT PLAYED_ON, HOME_TEAM_NAME, ATTENDANCE
    FROM TEAM_SUMMARY
    WHERE HOME_TEAM_NAME IN ({','.join([f"'{team}'" for team in teams])})
    ORDER BY PLAYED_ON
    """
    return run_query(query)


def fetch_team_match_data():
    # Establish Snowflake connection
    conn = snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"]
    )
    # Query the TEAM_SUMMARY table
    query = """
    SELECT 
        MATCH_ID,
        HOME_TEAM_NAME AS TEAM_NAME,
        HOME_TEAM_SCORE AS TEAM_SCORE,
        AWAY_TEAM_NAME AS OPPONENT_TEAM,
        AWAY_TEAM_SCORE AS OPPONENT_SCORE,
        'Home' AS HOME_AWAY,
        PLAYED_ON AS GAME_DATE,
        LEAGUE_NAME
    FROM TEAM_SUMMARY
    WHERE WAS_GAME_POSTPONED = FALSE

    UNION ALL

    SELECT 
        MATCH_ID,
        AWAY_TEAM_NAME AS TEAM_NAME,
        AWAY_TEAM_SCORE AS TEAM_SCORE,
        HOME_TEAM_NAME AS OPPONENT_TEAM,
        HOME_TEAM_SCORE AS OPPONENT_SCORE,
        'Away' AS HOME_AWAY,
        PLAYED_ON AS GAME_DATE,
        LEAGUE_NAME
    FROM TEAM_SUMMARY
    WHERE WAS_GAME_POSTPONED = FALSE
    """
    # Execute the query and fetch data
    data = pd.read_sql(query, conn)

    # Close the connection
    conn.close()

    return data


# Function to get the last N games for each team
# Function to get the last N games for each team
def get_form_data(last_n_games):
    # Fetch match data dynamically from Snowflake
    match_data = fetch_team_match_data()

    # Ensure only the last N games for each team are considered
    match_data["GAME_DATE"] = pd.to_datetime(match_data["GAME_DATE"])
    match_data = match_data.sort_values(by=["TEAM_NAME", "GAME_DATE"], ascending=[True, False])
    match_data = match_data.groupby("TEAM_NAME").head(last_n_games).reset_index(drop=True)

    return match_data


# Function to apply filters for Form Analysis
def apply_filters(data, result_conditions):
    filtered_data = data.copy()

    # Filter by result conditions
    for result_type, count in result_conditions:
        if result_type.lower() == "win":
            filtered_data = filtered_data.groupby("TEAM_NAME").filter(
                lambda x: sum(x["TEAM_SCORE"] > x["OPPONENT_SCORE"]) >= count
            )
        elif result_type.lower() == "draw":
            filtered_data = filtered_data.groupby("TEAM_NAME").filter(
                lambda x: sum(x["TEAM_SCORE"] == x["OPPONENT_SCORE"]) >= count
            )
        elif result_type.lower() == "loss":
            filtered_data = filtered_data.groupby("TEAM_NAME").filter(
                lambda x: sum(x["TEAM_SCORE"] < x["OPPONENT_SCORE"]) >= count
            )

    return filtered_data


# Main app function
def main():
    st.title("Football Analytics")
    st.markdown(
        """Use the Tool bar on the left to select the application you like to use
        """
    )

    # Sidebar for toggling between apps
    app_options = ["Attendance Analysis", "Result Analysis", "Player Analysis"]
    selected_app = st.sidebar.selectbox("Select an App", app_options)

    if selected_app == "Attendance Analysis":
        st.subheader("Attendance Analysis")
        st.markdown(
            """Select the League and then the teams you would like to see the attendance for. The Tool will then generate a line graph showing the team or teams attendance over time.
            """
        )

        # Step 1: Fetch unique leagues and teams
        data = get_unique_leagues_and_teams()
        leagues = data["LEAGUE_NAME"].unique()
        teams_by_league = {league: data[data["LEAGUE_NAME"] == league]["HOME_TEAM_NAME"].tolist() for league in leagues}

        # Step 2: League and team selection
        st.subheader("Select Teams")

        # Allow users to select leagues first (optional)
        selected_leagues = st.multiselect(
            "Filter by Leagues (Optional)",
            options=leagues,
            default=[],  # Empty by default to show all teams
            help="Select one or more leagues to filter available teams."
        )

        # Filter teams based on selected leagues
        if selected_leagues:
            available_teams = [
                team for league in selected_leagues for team in teams_by_league[league]
            ]
        else:
            # Show all teams if no league is selected
            available_teams = data["HOME_TEAM_NAME"].unique()

        # Allow users to select multiple teams across leagues
        selected_teams = st.multiselect(
            "Select Teams to Compare Attendance",
            options=available_teams,
            default=[],  # Start with no teams selected
            help="You can select teams from multiple leagues for comparison."
        )

        # Step 3: Display attendance trends for selected teams
        if selected_teams:
            st.subheader("Attendance Trends")
            attendance_data = get_attendance_data(selected_teams)

            if not attendance_data.empty:
                # Plot the attendance trends
                fig = px.line(
                    attendance_data,
                    x="PLAYED_ON",
                    y="ATTENDANCE",
                    color="HOME_TEAM_NAME",
                    title="Attendance Over Time",
                    labels={"PLAYED_ON": "Date", "ATTENDANCE": "Attendance", "HOME_TEAM_NAME": "Team"}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data available for the selected teams.")
        else:
            st.warning("Please select at least one team to view the attendance trends.")

    elif selected_app == "Result Analysis":
        st.subheader("Result Analysis")
        st.markdown(
            """How It Works. As a user, you will select the game interval to analyze. For example, if you choose **5 games**, the tool will focus on the last 5 games each team has played.  
            You can then define conditions to filter teams based on performance. For instance, you might specify that a team must have **at least 3 wins** and **at least 1 draw** during the selected interval.  
            Tip: Once Happy with Criteria Press **Show me Results** to return the games.
            """
        )
        num_games = st.number_input(
            "Select Amount of Games",
            min_value=1,
            max_value=20,
            value=5,
            help="Choose how many of each team's last games (home and away) you want to analyze."
        )

        # Dynamic rows for result conditions
        if "result_conditions" not in st.session_state:
            st.session_state.result_conditions = [{"type": "Win", "count": 1}]

        # Add and remove buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Add Condition") and len(st.session_state.result_conditions) < 3:
                st.session_state.result_conditions.append({"type": "Win", "count": 1})
        with col2:
            if st.button("Remove Condition") and len(st.session_state.result_conditions) > 1:
                st.session_state.result_conditions.pop()

        # Display result condition rows
        result_conditions = []
        for i, condition in enumerate(st.session_state.result_conditions):
            cols = st.columns([2, 1])
            with cols[0]:
                result_type = st.selectbox(
                    f"Result Type (Condition {i + 1})",
                    options=["Win", "Draw", "Loss"],
                    index=["Win", "Draw", "Loss"].index(condition["type"]),
                    key=f"result_type_{i}"
                )
            with cols[1]:
                result_count = st.number_input(
                    f"Count (Condition {i + 1})",
                    min_value=0,
                    value=condition["count"],
                    key=f"result_count_{i}"
                )
            result_conditions.append((result_type, result_count))

        # Update session state with the latest conditions
        st.session_state.result_conditions = [
            {"type": result_type, "count": result_count} for result_type, result_count in result_conditions
        ]

        # Step 3: Analyze Data Based on Conditions
        if st.button("Show me Results"):
            # Fetch and filter data dynamically
            form_data = get_form_data(last_n_games=num_games)
            filtered_data = apply_filters(form_data, result_conditions)

            # Display results
            if not filtered_data.empty:
                st.subheader("Match Results By Team")

                # Transform data for desired output
                filtered_data = filtered_data.sort_values(by=["TEAM_NAME", "GAME_DATE"])

                # Extract relevant columns and modify as needed
                table_data = pd.DataFrame({
                    "TeamName": filtered_data["TEAM_NAME"],
                    "PlayedOn": filtered_data["GAME_DATE"].dt.date,  # Convert datetime to date
                    "Home": filtered_data.apply(
                        lambda x: x["TEAM_NAME"] if x["HOME_AWAY"] == "Home" else x["OPPONENT_TEAM"], axis=1
                    ),
                    "HomeScore": filtered_data.apply(
                        lambda x: x["TEAM_SCORE"] if x["HOME_AWAY"] == "Home" else x["OPPONENT_SCORE"], axis=1
                    ),
                    "Away": filtered_data.apply(
                        lambda x: x["TEAM_NAME"] if x["HOME_AWAY"] == "Away" else x["OPPONENT_TEAM"], axis=1
                    ),
                    "AwayScore": filtered_data.apply(
                        lambda x: x["TEAM_SCORE"] if x["HOME_AWAY"] == "Away" else x["OPPONENT_SCORE"], axis=1
                    ),
                })

                # Reset the index to ensure it is not displayed in the output table
                table_data = table_data.reset_index(drop=True)

                # Add visibility for built-in features
                st.write("""
                    **💡 Hoover Over table column to get additional features**:
                    """)

                # Display the table
                st.dataframe(table_data, use_container_width=True)

                # Add a custom download button
                csv = table_data.to_csv(index=False)
                st.download_button(
                    label="📥 Download Table as CSV",
                    data=csv,
                    file_name="match_results.csv",
                    mime="text/csv",
                )
            else:
                st.warning("No teams match the specified criteria. Try adjusting your filters.")

    elif selected_app == "Player Analysis":
        st.header("Player Analysis")
        st.write("Player Analysis functionality will be implemented here.")


# Run the app
if __name__ == "__main__":
    main()






# CALLBACKS
# -----------------------------------------------------------------------------

