from utils import run_query
import streamlit as st
import pandas as pd

def get_team_filters():
    query = """
    SELECT DISTINCT 
        DT.COUNTRY_NAME, 
        DL.SHORT_NAME AS LEAGUE_NAME, 
        DT.TEAM_NAME 
    FROM DIM_TEAMS DT
    JOIN DIM_LEAGUES DL ON DT.LEAGUE_NAME = DL.LEAGUE_NAME
    """
    return run_query(query)

# Function to fetch team match statistics along with opponent names
def get_team_stats(team_name, num_games, game_role):
    query = f"""
    WITH RankedMatches AS (
        SELECT 
            FTM.GAME_ID,
            FTM.PLAYED_ON AS match_date,
            FTM.GAMEROLE AS team_role,
            FTM.SCORED AS goals_scored,
            FTM.CONCEEDED AS goals_conceded,
            ROW_NUMBER() OVER (PARTITION BY FTM.TEAM_ID ORDER BY FTM.PLAYED_ON DESC) AS game_rank
        FROM FACT_TEAM_MATCH FTM
        JOIN DIM_TEAMS DT ON FTM.TEAM_ID = DT.TEAM_ID
        WHERE DT.TEAM_NAME = '{team_name}' AND FTM.GAMEROLE = {game_role}
    )

    SELECT RM.match_date, RM.team_role, RM.goals_scored, RM.goals_conceded, Opponent.TEAM_NAME AS opponent
    FROM RankedMatches RM
    JOIN FACT_TEAM_MATCH OpponentMatch ON RM.GAME_ID = OpponentMatch.GAME_ID
    JOIN DIM_TEAMS Opponent ON OpponentMatch.TEAM_ID = Opponent.TEAM_ID
    WHERE OpponentMatch.GAMEROLE != RM.team_role
    AND {f"game_rank <= {num_games}" if num_games != "All" else "1=1"}
    ORDER BY match_date DESC;
    """

    df = run_query(query)
    df.columns = df.columns.str.lower()
    df = df.fillna(0)

    return df

# Function to format match history tables
def format_match_history(df, team_name, is_home):
    if df.empty:
        return df

    if is_home:
        df = df.rename(columns={
            "match_date": "Match Date",
            "goals_scored": "Home Score",
            "goals_conceded": "Away Score",
            "opponent": "Away Team"
        })
        df["Home Team"] = team_name
        df = df[["Match Date", "Home Team", "Home Score", "Away Score", "Away Team"]]
    else:
        df = df.rename(columns={
            "match_date": "Match Date",
            "goals_scored": "Away Score",
            "goals_conceded": "Home Score",
            "opponent": "Home Team"
        })
        df["Away Team"] = team_name
        df = df[["Match Date", "Home Team", "Home Score", "Away Score", "Away Team"]]

    return df

# Function to convert DataFrame into styled HTML table
def df_to_html_table(df, title):
    """Converts a Pandas DataFrame into a styled HTML table with no index."""
    if df.empty:
        return "<p style='color:red; font-weight:bold;'>No data available</p>"

    table_html = f"""
    <h3>{title}</h3>
    {df.to_html(index=False, escape=False, border=0, classes="styled-table")}
    """
    return table_html

# Global CSS for Styling
st.markdown("""
    <style>
        .styled-table {
            width: 100%;
            border-collapse: collapse;
            text-align: center;
            font-family: Arial, sans-serif;
        }
        .styled-table th {
            background-color: #003366;
            color: white;
            padding: 10px;
            border: 1px solid #ddd;
        }
        .styled-table td {
            padding: 8px;
            border: 1px solid #ddd;
        }
        .styled-table tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        h3 {
            text-align: center;
            color: #003366;
            margin-top: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# Streamlit UI for Goals Prediction
def goals_prediction():
    st.subheader("⚽ Goals Prediction")

    st.markdown("""
        Select upcoming matches by choosing Home and Away teams.  
        Predictions use **average goals scored and conceded** from:
        - **All Games**
        - **Last 10 Games**
        - **Last 5 Games**

        **Prediction Methods:**
        - **Generic Prediction** → Based on teams' average goals scored
        - **Weighted Prediction** → 60% Home Team’s Scored + 40% Away Team’s Conceded

        Press **Process Predictions** when ready.
    """, unsafe_allow_html=True)

    # Fetch available teams
    team_data = get_team_filters()

    if team_data.empty:
        st.error("❌ No team data found. Please check the data source.")
        return

    team_data.columns = team_data.columns.str.lower()

    # Country Selector
    selected_country = st.selectbox("🌍 Select Country", ["All"] + list(team_data["country_name"].unique()))

    # League Selector
    leagues = team_data["league_name"].unique() if selected_country == "All" else \
        team_data[team_data["country_name"] == selected_country]["league_name"].unique()
    selected_league = st.selectbox("🏆 Select League", ["All"] + list(leagues))

    # Team Selector
    teams = team_data["team_name"].unique() if selected_league == "All" else team_data[
        (team_data["country_name"] == selected_country) & (team_data["league_name"] == selected_league)
        ]["team_name"].unique()

    if len(teams) == 0:
        st.warning("⚠️ No teams available. Try selecting a different country or league.")
        return

    # Select Dataset Type
    selected_dataset = st.radio("📊 Select Data Type for Prediction", ["All Games", "Last 10 Games", "Last 5 Games"])

    # Set Number of Games Dynamically
    num_games = "All" if selected_dataset == "All Games" else 10 if selected_dataset == "Last 10 Games" else 5

    # Match Selection Inputs
    col1, col2 = st.columns([1, 1])
    with col1:
        home_team = st.selectbox("🏠 Home Team", ["Select"] + list(teams))
    with col2:
        away_team = st.selectbox("✈️ Away Team", ["Select"] + list(teams))

    # Process Button
    if st.button("⚡ Process Predictions"):
        if home_team == "Select" or away_team == "Select":
            st.warning("⚠️ Please select both Home and Away teams.")
            return

        # Fetch Home & Away Team Stats
        home_team_data = format_match_history(get_team_stats(home_team, num_games, game_role=1), home_team, is_home=True)
        away_team_data = format_match_history(get_team_stats(away_team, num_games, game_role=2), away_team, is_home=False)

        # **Calculate Predictions**
        predicted_home_goals_generic = round(home_team_data['Home Score'].mean(), 2)
        predicted_away_goals_generic = round(away_team_data['Away Score'].mean(), 2)

        predicted_home_goals_weighted = round(
            (0.7 * home_team_data['Home Score'].mean()) + (0.3 * away_team_data['Home Score'].mean()), 2)

        predicted_away_goals_weighted = round(
            (0.6 * away_team_data['Away Score'].mean()) + (0.4 * home_team_data['Away Score'].mean()), 2)

        # Display Predictions & Match History
        st.markdown(df_to_html_table(pd.DataFrame({"Home Team": [home_team], "Away Team": [away_team], "Predicted Home Goals": [predicted_home_goals_generic], "Predicted Away Goals": [predicted_away_goals_generic]}), "📋 Generic Prediction"), unsafe_allow_html=True)
        st.markdown(df_to_html_table(pd.DataFrame({"Home Team": [home_team], "Away Team": [away_team], "Predicted Home Goals": [predicted_home_goals_weighted], "Predicted Away Goals": [predicted_away_goals_weighted]}), "⚖️ Weighted Prediction"), unsafe_allow_html=True)

        st.markdown(df_to_html_table(home_team_data, f"🏠 {home_team} - Last {num_games} Home Games"), unsafe_allow_html=True)
        st.markdown(df_to_html_table(away_team_data, f"✈️ {away_team} - Last {num_games} Away Games"), unsafe_allow_html=True)

# Run Streamlit App
if __name__ == "__main__":
    goals_prediction()