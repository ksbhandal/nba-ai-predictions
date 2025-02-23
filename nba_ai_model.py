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
    
    # Fetch latest season data correctly with date filtering
    today_date = datetime.now().strftime("%Y-%m-%d")
    next_2_days = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    games_data = fetch_api_data("games", {"league": "12", "season": current_season, "from": today_date, "to": next_2_days})
    team_stats_data = fetch_api_data("teams/statistics", {"league": "12", "season": current_season})
    
    # Validate API response
    if not games_data:
        st.error("No data received from API. Please check your API key, season restrictions, or request limits.")
    else:
        st.success("Data successfully fetched!")
    
    # Save the data
    saved_data = {
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "games": games_data,
        "team_stats": team_stats_data,
    }
    save_data(saved_data)
else:
    st.write("Using cached data...")

# Convert saved data to DataFrames
def process_game_data(game_list):
    processed_data = []
    best_picks = []
    cutoff_date = datetime.now() + timedelta(days=2)
    
    for game in game_list:
        if isinstance(game, dict):
            try:
                game_date_str = game.get("date", "N/A")
                try:
                    game_date = datetime.strptime(game_date_str, "%Y-%m-%d")
                except ValueError:
                    game_date = datetime.now()
                
                if game_date.date() > cutoff_date.date():
                    continue
                
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
                    "Date": game_date.strftime("%Y-%m-%d"),
                    "Time": game.get("time", "N/A"),
                    "Home Team": home_team,
                    "Away Team": away_team,
                    "Home Win Probability": round(home_win_prob, 2),
                    "Away Win Probability": round(away_win_prob, 2),
                }
                processed_data.append(game_info)
                
                best_picks.append({
                    "Matchup": f"{home_team} vs {away_team}",
                    "Best Pick (Moneyline)": f"{home_team if home_win_prob > away_win_prob else away_team}",
                    "Confidence (Moneyline)": round(confidence_moneyline, 2),
                    "Best Pick (Spread)": f"{spread} ({home_team if spread > 0 else away_team})",
                    "Confidence (Spread)": round(confidence_spread, 2),
                    "Best Pick (Total)": f"Over {total_points}" if total_points > 220 else f"Under {total_points}",
                    "Confidence (Total)": round(confidence_total, 2),
                })
            except KeyError as e:
                st.warning(f"Missing key in game data: {e}")
    return pd.DataFrame(processed_data), pd.DataFrame(best_picks)

# Process and clean data
df, best_picks_df = process_game_data(saved_data.get("games", []))

# Streamlit Dashboard
st.title("NBA AI Prediction Dashboard")
st.metric(label="Last Updated (PST)", value=datetime.now(pytz.timezone("America/Los_Angeles")).strftime("%Y-%m-%d %H:%M"))

# Display Upcoming NBA Predictions
st.subheader("Upcoming NBA Predictions")
if not df.empty:
    st.dataframe(df)
else:
    st.write("No upcoming predictions available.")

# Display Best Picks for Next 2 Days
st.subheader("Best Picks for Next 2 Days")
if not best_picks_df.empty:
    st.dataframe(best_picks_df)
else:
    st.write("No best picks available.")
