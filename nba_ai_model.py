import os
import requests
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV
import datetime
import matplotlib.pyplot as plt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Ensure required packages are installed
os.system("pip install requests pandas numpy streamlit plotly scikit-learn matplotlib")

def fetch_api_data(url, params=None):
    """Fetch API data with error handling"""
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error for HTTP failures
        return response.json()  # Ensure response is JSON
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return {}  # Return empty dictionary to prevent crashes
    except ValueError:
        st.error("Invalid JSON response from API")
        return {}

# Step 1: Fetch NBA Data (Current Season)
current_season = datetime.datetime.now().year
if current_season > 2024:
    current_season = 2024  # Use latest available season

NBA_API_URL = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{current_season}-01-01"
params = {"key": "YOUR_NEW_API_KEY"}  # Replace with a valid API key
data = fetch_api_data(NBA_API_URL, params).get("data", [])

# Convert to DataFrame
df = pd.DataFrame(data)

# Fetch Real-Time NBA Data
LIVE_NBA_API_URL = "https://api.sportsdata.io/v3/nba/scores/json/AreAnyGamesInProgress"
live_data = fetch_api_data(LIVE_NBA_API_URL, params)
live_df = pd.DataFrame(live_data)

# Fetch Player Stats
PLAYER_STATS_API = "https://api.sportsdata.io/v3/nba/stats/json/PlayerSeasonStats/{current_season}"
player_data = fetch_api_data(PLAYER_STATS_API, params).get("data", [])
player_df = pd.DataFrame(player_data)

# Ensure Data Exists Before Feature Engineering
if not df.empty:
    df["home_win"] = df["HomeTeamScore"] > df["AwayTeamScore"]
    df["point_diff"] = df["HomeTeamScore"] - df["AwayTeamScore"]
    df["pace"] = (df["HomeTeamScore"] + df["AwayTeamScore"]) / 2
    df["home_last_15_avg"] = df["HomeTeamScore"].rolling(window=15).mean()
    df["away_last_15_avg"] = df["AwayTeamScore"].rolling(window=15).mean()

# Streamlit Dashboard
st.title("NBA AI Prediction Dashboard")
st.metric(label="Optimized Model Accuracy", value=f"N/A")

# Display Real-Time Games Data
st.subheader("Live NBA Games")
if not live_df.empty:
    st.write("Games are currently in progress!")
else:
    st.write("No live games available.")

# Display NBA Data Table
st.subheader("NBA Game Data")
if not df.empty:
    st.dataframe(df)
else:
    st.write("No game data available.")
