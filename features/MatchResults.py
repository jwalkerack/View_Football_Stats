import streamlit as st
import pandas as pd
from utils import run_query  # Ensure you have a run_query function that connects to Snowflake


# Function to fetch team results based on user input

def fetch_team_results(num_games, result_conditions):
    """
    Queries Snowflake to retrieve aggregated win/loss/draw counts
    for each team over the last `num_games` matches.

    Args:
        num_games (int): The number of past games to analyze.
        result_conditions (list): List of tuples containing conditions like [("Win", 5), ("Loss", 2)].

    Returns:
        pd.DataFrame: Aggregated results from Snowflake.
    """

    # Build WHERE clause dynamically based on user input
    condition_clauses = []
    for result_type, min_count in result_conditions:
        if result_type.lower() == "win":
            condition_clauses.append(f"AR.total_wins >= {min_count}")
        elif result_type.lower() == "loss":
            condition_clauses.append(f"AR.total_losses >= {min_count}")
        elif result_type.lower() == "draw":
            condition_clauses.append(f"AR.total_draws >= {min_count}")

    where_clause = " AND ".join(condition_clauses) if condition_clauses else "1=1"

    # **Fixed SQL Query**
    query = f"""
WITH RankedGames AS (
    SELECT 
        TEAM_ID, 
        GAME_NUMBER,
        CASE 
            WHEN GAMEROLE = 1 AND POINTS = 3 THEN 'win'
            WHEN GAMEROLE = 1 AND POINTS = 0 THEN 'loss'
            WHEN GAMEROLE = 1 AND POINTS = 1 THEN 'draw'
            WHEN GAMEROLE = 2 AND POINTS = 3 THEN 'win'
            WHEN GAMEROLE = 2 AND POINTS = 0 THEN 'loss'
            WHEN GAMEROLE = 2 AND POINTS = 1 THEN 'draw'
            ELSE 'unknown'
        END AS match_result,
        ROW_NUMBER() OVER (PARTITION BY TEAM_ID ORDER BY GAME_NUMBER DESC) AS game_rank
    FROM FACT_TEAM_MATCH
),

FilteredGames AS (
    SELECT * FROM RankedGames WHERE game_rank <= {num_games}
),

AggregatedResults AS (
    SELECT
        TEAM_ID,
        COUNT(*) AS games,
        SUM(CASE WHEN match_result = 'win' THEN 1 ELSE 0 END) AS total_wins,
        SUM(CASE WHEN match_result = 'loss' THEN 1 ELSE 0 END) AS total_losses,
        SUM(CASE WHEN match_result = 'draw' THEN 1 ELSE 0 END) AS total_draws
    FROM FilteredGames
    GROUP BY TEAM_ID
)

SELECT 
    AR.TEAM_ID,
    DM.TEAM_NAME,
    DM.LEAGUE_NAME,
    AR.games,
    AR.total_wins,
    AR.total_losses,
    AR.total_draws
FROM AggregatedResults AR
LEFT JOIN DIM_TEAMS DM
    ON AR.TEAM_ID = DM.TEAM_ID
WHERE {where_clause} AND AR.games >= {num_games}  -- ✅ Ensures teams have at least `num_games`
ORDER BY AR.total_wins DESC;

    """

    # Execute the query
    df = run_query(query)

    # ✅ Convert all column names to lowercase for consistency
    df.columns = df.columns.str.lower()

    # ✅ Debugging: Print the cleaned column names
    print("DEBUG: Cleaned Column Names:", df.columns.tolist())

    return df




# Function to display results in a properly formatted table
def display_results_table(df):
    """Formats and displays results as a table in Streamlit."""
    if df.empty:
        st.warning("❌ No teams match the specified conditions.")
        return

    # ✅ Debugging: Print column names before accessing them
    print("DEBUG: Displaying table with columns:", df.columns.tolist())

    # Define required columns
    required_columns = ['team_name', 'league_name', 'games', 'total_wins', 'total_losses',
                        'total_draws']

    # Check if required columns exist
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        st.error(f"❌ Missing expected columns in the data: {missing_columns}")
        return

    # Convert dataframe to HTML with custom styling
    table_html = df[required_columns].to_html(index=False, escape=False)

    # Display the table using Streamlit write function
    st.write(table_html, unsafe_allow_html=True)


# Streamlit UI for result analysis
def result_analysis():
    st.subheader("📊 Result Analysis")

    st.markdown("""
        **How It Works:**  
        - Select how many past games to analyze per team.  
        - Define **win/draw/loss** conditions to filter the results.  
        - The system will later filter teams that meet these conditions.  
    """)

    # User input for number of games to analyze
    num_games = st.number_input(
        "🎮 Select Number of Past Games to Analyze",
        min_value=1,
        max_value=20,
        value=5,
        help="Choose how many of each team's last games to include in the analysis."
    )

    # Initialize session state for result conditions
    if "result_conditions" not in st.session_state:
        st.session_state.result_conditions = [{"type": "Win", "count": 1}]

    # Buttons to add/remove conditions
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("➕ Add Condition") and len(st.session_state.result_conditions) < 3:
            st.session_state.result_conditions.append({"type": "Win", "count": 1})
    with col2:
        if st.button("🗑 Remove Condition") and len(st.session_state.result_conditions) > 1:
            st.session_state.result_conditions.pop()

    # Display dynamic result condition rows
    result_conditions = []
    for i, condition in enumerate(st.session_state.result_conditions):
        cols = st.columns([2, 1])
        with cols[0]:
            result_type = st.selectbox(
                f"Condition {i + 1}: Result Type",
                options=["Win", "Draw", "Loss"],
                index=["Win", "Draw", "Loss"].index(condition["type"]),
                key=f"result_type_{i}"
            )
        with cols[1]:
            result_count = st.number_input(
                f"Condition {i + 1}: Minimum Count",
                min_value=0,
                value=condition["count"],
                key=f"result_count_{i}"
            )
        result_conditions.append((result_type, result_count))

    # Button to process results
    if st.button("📈 Show Results"):
        filtered_teams = fetch_team_results(num_games, result_conditions)

        if not filtered_teams.empty:
            st.subheader("📊 Teams Matching Criteria")
            display_results_table(filtered_teams)
        else:
            st.warning("❌ No teams match the specified conditions.")
