# Football UK Streamlit App ⚽  

This repository contains the source code for the **Football UK Streamlit** application.  

🔗 **Live App:** [footballuk.streamlit.app](https://footballuk.streamlit.app/)  

## Overview  
The application provides interactive football data analysis through various features. The codebase is organized into separate `.py` files, each corresponding to a specific feature. These features are then integrated into the main Streamlit app.  

## Features  

- **League Table Builder** 📊  
  Users can select and generate different league tables based on various criteria.  

- **Attendance Analysis** 📉  
  Users can select teams and track their attendance trends over time.  

- **Team Form Analysis** 📈  
  Allows users to define criteria and find teams that match specific performance conditions.  

- **Goals Prediction** ⚽🔮  
  Given a match, this feature predicts expected goals for both teams based on historical home and away performances.  

- **Player Actions Analysis** 🎯  
  Users can analyze player goal contributions (goals & assists) plotted across the minutes they have played.  

## Technology Stack  

- **Frontend:** Streamlit  
- **Backend:** Python  
- **Database:** Snowflake  
- **Data Processing:** Pandas, SQL  

## Data Handling  
- The app primarily relies on **Snowflake** for data storage, with many features performing light data pulls from pre-aggregated tables.  
- Some features involve complex data joins, such as in **Goals Prediction**, where historical match performance is used to estimate expected goals.  

## Installation & Usage  
To run the app locally, follow these steps:  

### **1. Clone the repository**  
```bash
git clone https://github.com/your-repo-name.git
cd your-repo-name
