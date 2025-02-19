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

def fetch_api_data(url, headers=None):
    """Fetch API data with error handling"""
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for HTTP failures
        return response.json()  # Ensure response is JSON
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return {}  # Return empty dictionary to prevent crashes
    except ValueError:
        st.error("Invalid JSON response from API")
        return {}

# Step 1: Fetch NBA Data (Current Season) using ESPN API
ESPN_API_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
data = fetch_api_data(ESPN_API_URL).get("events", [])

# Convert to DataFrame
df = pd.json_normalize(data)

# Fetch Real-Time NBA Data
LIVE_NBA_API_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
live_data = fetch_api_data(LIVE_NBA_API_URL).get("events", [])
live_df = pd.json_normalize(live_data)

# Fetch Player Stats (Using ESPN API for Box Score Data)
PLAYER_STATS_API = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary"
player_data = fetch_api_data(PLAYER_STATS_API).get("boxscore", {}).get("players", [])
player_df = pd.json_normalize(player_data)

# Ensure Data Exists Before Feature Engineering
if not df.empty:
    df["home_team"] = df["competitions[0].competitors[0].team.displayName"]
    df["away_team"] = df["competitions[0].competitors[1].team.displayName"]
    df["home_score"] = df["competitions[0].competitors[0].score"]
    df["away_score"] = df["competitions[0].competitors[1].score"]
    df["point_diff"] = df["home_score"].astype(int) - df["away_score"].astype(int)
    df["game_status"] = df["status.type.name"]

# Streamlit Dashboard
st.title("NBA AI Prediction Dashboard")
st.metric(label="Optimized Model Accuracy", value=f"N/A")

# Display Real-Time Games Data
st.subheader("Live NBA Games")
if not live_df.empty:
    st.dataframe(live_df[["home_team", "away_team", "home_score", "away_score", "game_status"]])
else:
    st.write("No live games available.")

# Display NBA Data Table
st.subheader("NBA Game Data")
if not df.empty:
    st.dataframe(df[["home_team", "away_team", "home_score", "away_score", "point_diff", "game_status"]])
else:
    st.write("No game data available.")
