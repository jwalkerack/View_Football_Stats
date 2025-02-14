import streamlit as st
import pandas as pd
import snowflake.connector


# Snowflake connection function
def get_snowflake_connection():
    return snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"]
    )


# Fetch unique countries (optional filter)
@st.cache_data(ttl=600)
def get_countries():
    conn = get_snowflake_connection()
    query = "SELECT DISTINCT country_name FROM dim_leagues ORDER BY country_name;"

    # Execute the query directly
    cursor = conn.cursor()
    cursor.execute(query)
    raw_data = cursor.fetchall()  # Fetch all results

    # Print raw data for debugging
    print("Raw Query Results:", raw_data)

    # Convert raw tuples to a list of country names
    country_list = [row[0] for row in raw_data]

    # Close connection
    cursor.close()
    conn.close()

    return country_list  # Return just the list, not a DataFrame


# Fetch leagues based on selected country (or all leagues if no filter)
@st.cache_data(ttl=600)
def get_leagues(selected_country=None):
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    # Construct SQL query
    if selected_country and selected_country != "All":
        query = f"SELECT DISTINCT league_name FROM dim_leagues WHERE country_name = '{selected_country}' ORDER BY league_name;"
    else:
        query = "SELECT DISTINCT league_name FROM dim_leagues ORDER BY league_name;"

    # Execute the query
    cursor.execute(query)
    raw_data = cursor.fetchall()  # Fetch all results

    # Print raw data for debugging
    print("Raw Query Results for Leagues:", raw_data)

    # Convert list of tuples to a clean list of league names
    league_list = [row[0] for row in raw_data]

    # Close connection
    cursor.close()
    conn.close()

    return league_list  # Return just the list, not a DataFrame


# Fetch league standings with selected attributes

@st.cache_data(ttl=600)
def get_league_table(selected_league):
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    query = """
        SELECT 
            team_name AS Team_Name,
            GamesPlayed AS Played,
            TOTALPOINTS AS Points,
            WINS,
            DRAWS,
            LOSSES,
            TOTALSCORED AS GOALS,
            TOTALCONCEDED AS CONCEEDED
        FROM agg_league 
        WHERE FORMAL_LEAGUE_NAME = %s
        ORDER BY Points DESC;
    """

    # Execute query securely using parameterized query
    cursor.execute(query, (selected_league,))
    raw_data = cursor.fetchall()  # Fetch results

    # Print raw data for debugging
    print("Raw Query Results for League Table:", raw_data)

    # Convert to DataFrame with correct column names
    df = pd.DataFrame(raw_data, columns=[desc[0] for desc in cursor.description])

    # Close connection
    cursor.close()
    conn.close()

    return df


# Main function for the League Standings page
def leagues():
    st.title("🏆 Football League Table Viewer")
    test_connection()

    # Country filter (optional)
    selected_country = st.selectbox("🌍 Select Country (Optional)", ["All"] + get_countries())

    # Fetch leagues based on selection
    leagues_list = get_leagues(selected_country)

    # League selection
    selected_league = st.selectbox("⚽ Select League", leagues_list)

    # Fetch and display league table
    if selected_league:
        league_table = get_league_table(selected_league)

        if league_table.empty:
            st.warning("⚠ No data available for this league.")
        else:
            st.subheader(f"📊 {selected_league} Standings")

            # Custom Styled Table Display
            st.markdown(
                """
                <style>
                    table {
                        width: 100%;
                        border-collapse: collapse;
                    }
                    th, td {
                        padding: 10px;
                        border: 1px solid #ddd;
                        text-align: center;
                    }
                    th {
                        background-color: #003366;
                        color: white;
                    }
                    tr:nth-child(even) {
                        background-color: #f2f2f2;
                    }
                </style>
                """,
                unsafe_allow_html=True
            )

            st.write(league_table.to_html(index=False, escape=False), unsafe_allow_html=True)

def test_connection():
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_USER(), CURRENT_DATABASE(), CURRENT_SCHEMA();")
        print(cursor.fetchall())
        cursor.close()
        conn.close()
        print("✅ Snowflake connection successful!")
    except Exception as e:
        print(f"❌ Snowflake connection failed: {e}")


