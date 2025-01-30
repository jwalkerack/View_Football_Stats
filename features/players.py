import pandas as pd
import streamlit as st
import plotly.express as px
from utils import run_query, get_team_filters, get_player_stats


def apply_filters(players_df, filters):
    # Apply active filters
    for key, value in filters.items():
        if value['enabled_min']:
            players_df = players_df[players_df[key] >= value['min']]
        if value['enabled_max']:
            players_df = players_df[players_df[key] <= value['max']]
    return players_df


def visualize_good_performers(players_df):
    if players_df.empty:
        st.warning("⚠️ No players meet the criteria.")
        return

    players_df["G90"] = pd.to_numeric(players_df["G90"], errors="coerce")
    players_df["T_GOALS"] = pd.to_numeric(players_df["T_GOALS"], errors="coerce")
    players_df["T_MINUTES_PLAYED"] = pd.to_numeric(players_df["T_MINUTES_PLAYED"], errors="coerce")
    players_df["T_GAMES_PLAYED"] = pd.to_numeric(players_df["T_GAMES_PLAYED"], errors="coerce")
    players_df = players_df.dropna(subset=["G90", "T_GOALS", "T_MINUTES_PLAYED", "T_GAMES_PLAYED"])

    avg_goals = players_df["T_GOALS"].mean()
    avg_g90 = players_df["G90"].mean()

    fig = px.scatter(
        players_df, x="T_GOALS", y="G90",
        size="T_MINUTES_PLAYED", color="TEAM_NAME",
        hover_data={"PLAYER_NAME": True, "TEAM_NAME": True, "T_GAMES_PLAYED": True, "T_GOALS": True,
                    "T_MINUTES_PLAYED": True},
        title="Players Pivot",
        labels={"T_GOALS": "Total Goals", "G90": "Goals per 90 Minutes", "TEAM_NAME": "Team"}
    )

    fig.add_hline(y=avg_g90, line_dash="dash", line_color="gray", annotation_text="League Avg G90",
                  annotation_position="bottom right")
    fig.add_vline(x=avg_goals, line_dash="dash", line_color="gray", annotation_text="League Avg Goals",
                  annotation_position="top left")

    st.plotly_chart(fig)


def players_analysis():


    team_filters = get_team_filters()
    countries = team_filters['COUNTRY_NAME'].unique()
    selected_country = st.selectbox("🌍 Select Country", options=["Select"] + list(countries), index=0)

    leagues = []
    if selected_country != "Select":
        leagues = team_filters[team_filters['COUNTRY_NAME'] == selected_country]['LEAGUE_NAME'].unique()

    selected_league = st.selectbox("🏆 Select League", options=["Select"] + list(leagues), index=0)

    if st.button("🔍 Load Player Data"):
        players_df = get_player_stats(selected_country, selected_league)

        if players_df.empty:
            st.error("⚠️ No player data found! Please check your selection or data source.")
        else:
            st.session_state["players_df"] = players_df
            st.success("✅ Player data loaded successfully!")

    if "players_df" in st.session_state:
        players_df = st.session_state["players_df"]
    else:
        st.warning("⚠️ Please load player data first.")
        return

    st.sidebar.subheader("⚙️ Set Your Filters")

    filters = {
        "T_GAMES_PLAYED": {"label": "Games Played", "min": 10, "max": 50, "enabled_min": False, "enabled_max": False},
        "T_GOALS": {"label": "Total Goals", "min": 0, "max": 50, "enabled_min": False, "enabled_max": False},
        "GPG": {"label": "Goals Per Game", "min": 0.5, "max": 2.0, "enabled_min": False, "enabled_max": False},
        "G90": {"label": "Goals Per 90 Minutes", "min": 0.5, "max": 2.0, "enabled_min": False, "enabled_max": False}
    }

    for key, filter_data in filters.items():
        st.sidebar.markdown(f"**{filter_data['label']}**")
        filters[key]["enabled_min"] = st.sidebar.checkbox(f"Min {filter_data['label']}",
                                                          value=filter_data["enabled_min"])
        if filters[key]["enabled_min"]:
            filters[key]["min"] = st.sidebar.number_input(f"Min {filter_data['label']}", value=filter_data["min"],
                                                          format="%.2f" if isinstance(filter_data["min"],
                                                                                      float) else "%d")
        filters[key]["enabled_max"] = st.sidebar.checkbox(f"Max {filter_data['label']}",
                                                          value=filter_data["enabled_max"])
        if filters[key]["enabled_max"]:
            filters[key]["max"] = st.sidebar.number_input(f"Max {filter_data['label']}", value=filter_data["max"],
                                                          format="%.2f" if isinstance(filter_data["max"],
                                                                                      float) else "%d")

    if st.sidebar.button("Apply Filters"):
        active_filters = {k: v for k, v in filters.items() if v["enabled_min"] or v["enabled_max"]}
        filtered_players = apply_filters(players_df, active_filters)
        st.session_state["filtered_players"] = filtered_players

    if st.sidebar.button("Reset Filters"):
        if "filtered_players" in st.session_state:
            del st.session_state["filtered_players"]

    filtered_players = st.session_state.get("filtered_players", players_df)
    visualize_good_performers(filtered_players)
    csv = filtered_players.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(label="📥 Download Player Data", data=csv, file_name="players.csv", mime="text/csv")
