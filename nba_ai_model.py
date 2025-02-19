import os
os.system("pip install plotly")
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
NBA_API_URL = "https://www.balldontlie.io/api/v1/games"
params = {"seasons": [current_season], "per_page": 100}
data = fetch_api_data(NBA_API_URL, params).get("data", [])

# Convert to DataFrame
df = pd.DataFrame(data)

# Fetch Real-Time NBA Data
LIVE_NBA_API_URL = "https://www.balldontlie.io/api/v1/games/today"
live_data = fetch_api_data(LIVE_NBA_API_URL).get("data", [])
live_df = pd.DataFrame(live_data)

# Fetch Player Stats
PLAYER_STATS_API = "https://www.balldontlie.io/api/v1/stats"
player_data = fetch_api_data(PLAYER_STATS_API, {"seasons": [current_season], "per_page": 100}).get("data", [])
player_df = pd.DataFrame(player_data)

# Fetch Betting Odds
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
odds_params = {"regions": "us", "markets": "h2h,spreads,totals", "apiKey": "YOUR_API_KEY"}
odds_data = fetch_api_data(ODDS_API_URL, odds_params)
odds_df = pd.DataFrame(odds_data) if odds_data else pd.DataFrame()

# Ensure Data Exists Before Feature Engineering
if not df.empty:
    df["home_win"] = df["home_team_score"] > df["visitor_team_score"]
    df["point_diff"] = df["home_team_score"] - df["visitor_team_score"]
    df["home_offensive_rating"] = df["home_team_score"] / (df["home_team_score"] + df["visitor_team_score"])
    df["visitor_offensive_rating"] = df["visitor_team_score"] / (df["home_team_score"] + df["visitor_team_score"])
    df["pace"] = (df["home_team_score"] + df["visitor_team_score"]) / 2
    df["home_rebound_rate"] = df["home_team_score"] / df["point_diff"].abs()
    df["visitor_rebound_rate"] = df["visitor_team_score"] / df["point_diff"].abs()
    df["home_defensive_rating"] = 1 - df["visitor_offensive_rating"]
    df["visitor_defensive_rating"] = 1 - df["home_offensive_rating"]
    df["home_opponent_fg%"] = df["visitor_team_score"] / (df["home_team_score"] + df["visitor_team_score"])
    df["visitor_opponent_fg%"] = df["home_team_score"] / (df["home_team_score"] + df["visitor_team_score"])
    df["home_last_15_avg"] = df["home_team_score"].rolling(window=15).mean()
    df["visitor_last_15_avg"] = df["visitor_team_score"].rolling(window=15).mean()
    df["clutch_performance"] = (df["home_team_score"] - df["visitor_team_score"]).abs() / df["point_diff"]

# Compare AI Predictions with Betting Odds Safely
if 'best_model' in locals() and 'X' in locals():
    odds_df = odds_df.explode("bookmakers").reset_index()
    odds_df["predicted_winner"] = best_model.predict(X)
    odds_df["ai_confidence"] = best_model.predict_proba(X).max(axis=1)
    odds_df["bet_value"] = odds_df["ai_confidence"] - 0.5  # Identifying value bets
else:
    odds_df["predicted_winner"] = "Model Not Available"
    odds_df["ai_confidence"] = 0

# Streamlit Dashboard
st.title("NBA AI Prediction Dashboard")
st.metric(label="Optimized Model Accuracy", value=f"N/A")

# Display Betting Odds with AI Predictions
st.subheader("Betting Odds vs AI Predictions")
if not odds_df.empty:
    st.dataframe(odds_df[["bookmakers", "predicted_winner", "ai_confidence", "bet_value"]])
else:
    st.write("No betting odds available.")

# Display Real-Time Games Data
st.subheader("Live NBA Games")
if not live_df.empty:
    st.dataframe(live_df[["home_team.full_name", "visitor_team.full_name", "home_team_score", "visitor_team_score"]])
else:
    st.write("No live games available.")
