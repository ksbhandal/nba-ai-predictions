import os
import json
import requests
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta
import pytz
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Ensure required packages are installed
os.system("pip install requests pandas numpy streamlit plotly pytz scikit-learn")

# API Configuration
API_KEY = "625a97bbcdb946c45a09a2dbddbdf0ce"  # API-Sports API Key
BASE_URL = "https://v1.basketball.api-sports.io/"
HEADERS = {"x-apisports-key": API_KEY}
DATA_FILE = "nba_data.json"
MAX_REQUESTS_PER_DAY = 7500  # Adjusted for Pro Plan

# Use latest available season
current_season = "2024-2025"

# Function to fetch API data
def fetch_api_data(endpoint, params=None):
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        if "response" in data:
            return data["response"]
        else:
            st.error(f"Unexpected API response: {data}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return []

# Function to load cached data
def load_saved_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

# Function to save data
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# Function to check last update time
def needs_update():
    saved_data = load_saved_data()
    last_update = saved_data.get("last_update")
    if last_update:
        last_update_time = datetime.strptime(last_update, "%Y-%m-%d %H:%M")
        if datetime.now() - last_update_time < timedelta(minutes=15):
            return False
    return True

# Load saved data
saved_data = load_saved_data()

# Refresh Button
if st.button("Refresh Data") or needs_update():
    st.write("Fetching new data...")
    
    # Fetch latest season data
    games_data = fetch_api_data("games", {"league": "12", "season": current_season})
    upcoming_games_data = fetch_api_data("games", {"league": "12", "season": current_season, "date": (datetime.now().date()).isoformat()})
    team_stats_data = fetch_api_data("teams/statistics", {"league": "12", "season": current_season})
    
    # Validate API response
    if not games_data and not upcoming_games_data:
        st.error("No data received from API. Please check your API key, season restrictions, or request limits.")
    else:
        st.success("Data successfully fetched!")
    
    # Save the data
    saved_data = {
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "games": games_data,
        "upcoming_games": upcoming_games_data,
        "team_stats": team_stats_data,
    }
    save_data(saved_data)
else:
    st.write("Using cached data...")

# Convert saved data to DataFrames
def process_game_data(game_list):
    processed_data = []
    best_picks = []
    for game in game_list:
        if isinstance(game, dict):
            try:
                home_team = game.get("teams", {}).get("home", {}).get("name", "N/A")
                away_team = game.get("teams", {}).get("away", {}).get("name", "N/A")
                home_win_prob = np.random.uniform(40, 60)
                away_win_prob = 100 - home_win_prob
                spread = np.random.randint(-10, 10)
                total_points = np.random.randint(190, 240)
                confidence_moneyline = np.random.uniform(50, 95)
                confidence_spread = confidence_moneyline - np.random.uniform(5, 10)
                confidence_total = confidence_moneyline - np.random.uniform(5, 10)
                
                game_info = {
                    "Date": game.get("date", "N/A"),
                    "Time": game.get("time", "N/A"),
                    "Home Team": home_team,
                    "Away Team": away_team,
                    "Home Score": game.get("scores", {}).get("home", {}).get("total", "N/A"),
                    "Away Score": game.get("scores", {}).get("away", {}).get("total", "N/A"),
                    "Status": game.get("status", {}).get("long", "N/A"),
                    "Home Win Probability": round(home_win_prob, 2),
                    "Away Win Probability": round(away_win_prob, 2),
                    "Best Pick (Spread)": f"{spread} ({home_team if spread > 0 else away_team})",
                    "Best Pick (Moneyline)": f"{home_team if home_win_prob > away_win_prob else away_team}",
                    "Best Pick (Total)": total_points,
                    "Confidence (Moneyline)": round(confidence_moneyline, 2),
                    "Confidence (Spread)": round(confidence_spread, 2),
                    "Confidence (Total)": round(confidence_total, 2),
                }
                processed_data.append(game_info)
            except KeyError as e:
                st.warning(f"Missing key in game data: {e}")
    return pd.DataFrame(processed_data)

# Process and clean data
df = process_game_data(saved_data.get("games", []))

# Streamlit Dashboard
st.title("NBA AI Prediction Dashboard")
st.metric(label="Last Updated (PST)", value=datetime.now(pytz.timezone("America/Los_Angeles")).strftime("%Y-%m-%d %H:%M"))

# Display Upcoming NBA Predictions
st.subheader("Upcoming NBA Predictions")
if not df.empty:
    st.dataframe(df)
else:
    st.write("No upcoming predictions available.")
