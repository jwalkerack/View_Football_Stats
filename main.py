import streamlit as st
from features.attendance import attendance_analysis
from features.MatchResults import result_analysis
from features.GoalsPredication import goals_prediction
from features.players import players_analysis
from features.leagueTables import leagues
# Main app function
def main():
    st.title("Football Analytics")
    st.markdown(
        """Use the Tool bar on the left to select the application you like to use
        """
    )
    # Sidebar for toggling between apps
    app_options = ["League tables","Attendance analysis", "Team form analysis", "Goals prediction"]
    selected_app = st.sidebar.selectbox("Select an App", app_options)

    if selected_app == "League tables":
        leagues()
    elif  selected_app == "Attendance analysis":
        attendance_analysis()

    elif selected_app == "Team form analysis":
        result_analysis()

   # elif selected_app == "Player Analysis":
     #   st.header("Player Analysis")
     #   players_analysis()
    elif selected_app == "Goals prediction":
        goals_prediction()



# Run the app
if __name__ == "__main__":
    main()






# CALLBACKS
# -----------------------------------------------------------------------------

