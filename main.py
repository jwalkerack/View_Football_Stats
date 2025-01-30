import streamlit as st
from features.attendance import attendance_analysis
from features.MatchResults import result_analysis
from features.GoalsPredication import goals_prediction
from features.players import players_analysis

# Main app function
def main():
    st.title("Football Analytics")
    st.markdown(
        """Use the Tool bar on the left to select the application you like to use
        """
    )
    # Sidebar for toggling between apps
    app_options = ["Attendance Analysis", "Result Analysis", "Goals Prediction", "Player Analysis"]
    selected_app = st.sidebar.selectbox("Select an App", app_options)

    if selected_app == "Attendance Analysis":
        attendance_analysis()

    elif selected_app == "Result Analysis":
        result_analysis()

    elif selected_app == "Player Analysis":
        st.header("Player Analysis")
        players_analysis()
    elif selected_app == "Goals Prediction":
        goals_prediction()



# Run the app
if __name__ == "__main__":
    main()






# CALLBACKS
# -----------------------------------------------------------------------------

