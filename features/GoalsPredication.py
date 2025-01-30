
from utils import run_query , get_team_filters
import streamlit  as st
import pandas as pd
def get_team_attributes(team_name):
    query = f"""
    SELECT 
        TEAM_NAME, 
        AVG_HOME_GOALS_SCORED, 
        AVG_HOME_GOALS_CONCEDED, 
        AVG_AWAY_GOALS_SCORED, 
        AVG_AWAY_GOALS_CONCEDED
    FROM TEAM_AGGS
    WHERE TEAM_NAME = '{team_name}'
    """
    return run_query(query)

def goals_prediction():
    st.subheader("⚽ Goals Prediction")
    st.markdown(
        """Add up coming Games , Selecting Home and Away Teams. Predication takes  average/conceded for (home and away)  to generate score predications :home Score , Away Score and Total Goals. This takes the average the 
         teams have to date . Use Country and League to Filter teams to put into match , add multiple matches. Press process Predications when 
        ready. Option to download as csv
        """
    )

    # Fetch team filters from Snowflake
    team_data = get_team_filters()
    countries = team_data["COUNTRY_NAME"].unique()

    # Country Selector
    selected_country = st.selectbox("🌍 Select Country", options=["All"] + list(countries), index=0)

    # Filter leagues based on country
    leagues = team_data["LEAGUE_NAME"].unique() if selected_country == "All" else team_data[
        team_data["COUNTRY_NAME"] == selected_country]["LEAGUE_NAME"].unique()

    # League Selector
    selected_league = st.selectbox("🏆 Select League", options=["All"] + list(leagues), index=0)

    # Filter teams based on country & league
    teams = team_data["TEAM_NAME"].unique() if selected_league == "All" else team_data[
        (team_data["COUNTRY_NAME"] == selected_country) & (team_data["LEAGUE_NAME"] == selected_league)]["TEAM_NAME"].unique()

    # Initialize session state for storing multiple match rows
    if "match_rows" not in st.session_state:
        st.session_state.match_rows = [{"home_team": None, "away_team": None}]

    # Add and Remove Row Buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("➕ Add Match"):
            st.session_state.match_rows.append({"home_team": None, "away_team": None})
    with col2:
        if len(st.session_state.match_rows) > 1:
            if st.button("❌ Remove Last Match"):
                st.session_state.match_rows.pop()

    # Match Selection Inputs
    match_inputs = []
    for idx, match in enumerate(st.session_state.match_rows):
        cols = st.columns([1, 1])
        with cols[0]:
            home_team = st.selectbox(
                f"🏠 Home Team {idx+1}",
                options=["Select"] + list(teams),
                key=f"home_team_{idx}"
            )
        with cols[1]:
            away_team = st.selectbox(
                f"✈️ Away Team {idx+1}",
                options=["Select"] + list(teams),
                key=f"away_team_{idx}"
            )
        match_inputs.append((home_team, away_team))

    # Process Button
    if st.button("⚡ Process Predictions"):
        predictions = []

        for home_team, away_team in match_inputs:
            if home_team == "Select" or away_team == "Select":
                st.warning("⚠️ Please select both Home and Away teams for each match.")
                return

            # Fetch team stats
            home_team_data = get_team_attributes(home_team)
            away_team_data = get_team_attributes(away_team)

            if home_team_data.empty or away_team_data.empty:
                st.warning(f"❌ Data missing for {home_team} or {away_team}. Check data source.")
                return

            # Predict Scores
            predicted_home_goals = round(
                (home_team_data["AVG_HOME_GOALS_SCORED"].values[0] + away_team_data["AVG_AWAY_GOALS_CONCEDED"].values[0]) / 2, 2
            )
            predicted_away_goals = round(
                (away_team_data["AVG_AWAY_GOALS_SCORED"].values[0] + home_team_data["AVG_HOME_GOALS_CONCEDED"].values[0]) / 2, 2
            )
            total_goals_pred = predicted_home_goals + predicted_away_goals

            # Store full prediction info
            prediction = {
                "Home Team": home_team,
                "Away Team": away_team,
                "Predicted Home Goals": predicted_home_goals,
                "Predicted Away Goals": predicted_away_goals,
                "Total Goals Prediction": total_goals_pred,
                "Home Team Avg Home Goals": home_team_data["AVG_HOME_GOALS_SCORED"].values[0],
                "Home Team Avg Home Conceded": home_team_data["AVG_HOME_GOALS_CONCEDED"].values[0],
                "Away Team Avg Away Goals": away_team_data["AVG_AWAY_GOALS_SCORED"].values[0],
                "Away Team Avg Away Conceded": away_team_data["AVG_AWAY_GOALS_CONCEDED"].values[0],
            }
            predictions.append(prediction)

            # Display Match Prediction in Visual Boxes

            with st.container():
                st.info(
                    f"🏠 **{home_team}** vs ✈️ **{away_team}**  |  "
                    f"**Home Pred:** {predicted_home_goals}  |  "
                    f"**Away Pred:** {predicted_away_goals}  |  "
                    f"**Total Pred:** {total_goals_pred}"
                )

        # Convert results to DataFrame
        predictions_df = pd.DataFrame(predictions)

        # Display predictions table

        #st.dataframe(predictions_df, use_container_width=True)

        # Allow CSV download
        csv = predictions_df.to_csv(index=False)
        st.download_button("📥 Download Predictions as CSV", csv, "predictions.csv", "text/csv")