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





# Function to get the last N games for each team
# Function to get the last N games for each team



# Function to apply filters for Form Analysis



def get_team_filters():
    query = """
    SELECT DISTINCT COUNTRY_NAME, SHORT_NAME AS LEAGUE_NAME, TEAM_NAME 
    FROM DIM_TEAMS_V2
    """
    return run_query(query)


# Fetch team attributes from Team_Aggs view
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
