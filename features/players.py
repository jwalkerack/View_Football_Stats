import streamlit as st
import pandas as pd
import plotly.express as px
from utils import run_query


# Function to fetch available countries, leagues, and teams from `dim_teams`
def get_team_filters():
    query = """
    SELECT DISTINCT COUNTRY_NAME, LEAGUE_NAME, TEAM_ID, TEAM_NAME
    FROM dim_teams
    """
    df = run_query(query)
    df.columns = df.columns.str.lower()
    return df


# Function to fetch player stats from `agg_player`
def get_player_stats(selected_country, selected_league, selected_team):
    query = f"""
    SELECT 
        PLAYER_NAME, TEAM_NAME, COUNTRY_NAME, LEAGUE_NAME, 
        TOTAL_MINUTESPLAYED, TOTAL_GOALS, TOTAL_ASSISTS
    FROM agg_player
    WHERE COUNTRY_NAME = '{selected_country}'
    AND LEAGUE_NAME = '{selected_league}'
    {f"AND TEAM_NAME = '{selected_team}'" if selected_team else ""}
    """

    df = run_query(query)

    # Ensure proper data types
    df.columns = df.columns.str.lower()
    df = df.fillna(0)
    df["total_minutesplayed"] = pd.to_numeric(df["total_minutesplayed"], errors="coerce")
    df["total_goals"] = pd.to_numeric(df["total_goals"], errors="coerce")
    df["total_assists"] = pd.to_numeric(df["total_assists"], errors="coerce")

    # Add a new column for goal contributions (goals + assists)
    df["goal_contributions"] = df["total_goals"] + df["total_assists"]

    # 🔥 **Filter out players with zero goal contributions**
    df = df[df["goal_contributions"] > 0]

    return df


# Function to generate scatter plot
def plot_minutes_vs_goal_contributions(players_df):
    """Creates and displays a scatter plot of Minutes Played vs. Goal Contributions."""
    if players_df.empty:
        st.warning("⚠️ No player data available for the selected filters.")
        return

    # Scatter plot
    fig = px.scatter(
        players_df,
        x="total_minutesplayed",
        y="goal_contributions",
        size="goal_contributions",
        color="team_name",
        hover_data={"player_name": True, "team_name": True, "total_goals": True, "total_assists": True,
                    "total_minutesplayed": True},
        title="Minutes Played vs Goal Contributions",
        labels={"total_minutesplayed": "Total Minutes Played",
                "goal_contributions": "Goal Contributions (Goals + Assists)", "team_name": "Team"}
    )

    # Display plot
    st.plotly_chart(fig)


# Streamlit UI for Player Data Analysis
def players_analysis():
    st.subheader("⚽ Player Performance Analysis")

    # Fetch available teams and leagues
    team_filters = get_team_filters()

    countries = team_filters['country_name'].unique()

    # Country Selection
    selected_country = st.selectbox("🌍 Select Country", options=["Select"] + list(countries), index=0)

    leagues = []
    if selected_country != "Select":
        leagues = team_filters[team_filters['country_name'] == selected_country]['league_name'].unique()

    selected_league = st.selectbox("🏆 Select League", options=["Select"] + list(leagues), index=0)

    teams = []
    if selected_league != "Select":
        teams = team_filters[
            (team_filters['country_name'] == selected_country) & (team_filters['league_name'] == selected_league)][
            'team_name'].unique()

    selected_team = st.selectbox("🏟️ Select Team (Optional)", options=["All"] + list(teams), index=0)

    # Button to load data
    if st.button("📊 Load & Plot Data"):
        if selected_country == "Select" or selected_league == "Select":
            st.error("❌ Please select both a Country and League.")
            return

        # Fetch player data
        players_df = get_player_stats(selected_country, selected_league,
                                      selected_team if selected_team != "All" else "")

        if players_df.empty:
            st.error("⚠️ No player data found for the selected filters.")
        else:
            st.success("✅ Data loaded successfully! Generating visualization...")
            plot_minutes_vs_goal_contributions(players_df)


# Run Streamlit App
if __name__ == "__main__":
    players_analysis()
