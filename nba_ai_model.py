import os
import json
import requests
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from datetime import datetime, time
import pytz

# Ensure required packages are installed
os.system("pip install requests pandas numpy streamlit plotly pytz")

# API Configuration
API_KEY = "625a97bbcdb946c45a09a2dbddbdf0ce"  # API-Sports API Key
BASE_URL = "https://v1.basketball.api-sports.io/"
HEADERS = {
    "x-apisports-key": API_KEY
}
DATA_FILE = "nba_data.json"
UPDATE_TIMES = ["07:00", "12:00", "15:00", "22:00"]

# Function to fetch API data
def fetch_api_data(endpoint, params=None):
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("response", [])
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

# Determine if an update is needed
def is_update_time():
    current_time = datetime.now().strftime("%H:%M")
    return current_time in UPDATE_TIMES

# Load saved data
saved_data = load_saved_data()

if "last_update" not in saved_data or is_update_time():
    st.write("Fetching new data...")
    current_season = datetime.now().year if datetime.now().month > 6 else datetime.now().year - 1
    
    # Fetch data
    games_data = fetch_api_data("games", {"league": "12", "season": current_season})  # NBA League ID = 12
    live_games_data = fetch_api_data("games", {"league": "12", "season": current_season, "live": "all"})
    upcoming_games_data = fetch_api_data("games", {"league": "12", "season": current_season, "date": (datetime.now().date()).isoformat()})
    player_stats_data = fetch_api_data("players/statistics", {"league": "12", "season": current_season})
    
    # Save the data
    saved_data = {
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "games": games_data,
        "live_games": live_games_data,
        "upcoming_games": upcoming_games_data,
        "player_stats": player_stats_data,
    }
    save_data(saved_data)
else:
    st.write("Using cached data...")

# Convert saved data to DataFrames
df = pd.DataFrame(saved_data.get("games", []))
live_df = pd.DataFrame(saved_data.get("live_games", []))
upcoming_df = pd.DataFrame(saved_data.get("upcoming_games", []))
player_df = pd.DataFrame(saved_data.get("player_stats", []))

# Convert UTC to PST
utc_time = datetime.strptime(saved_data["last_update"], "%Y-%m-%d %H:%M")
pst_timezone = pytz.timezone("America/Los_Angeles")  # PST Timezone
pst_time = utc_time.astimezone(pst_timezone)

# Streamlit Dashboard
st.title("NBA AI Prediction Dashboard")
st.metric(label="Last Updated (PST)", value=pst_time.strftime("%Y-%m-%d %H:%M"))

# Display Live NBA Games
st.subheader("Live NBA Games")
if not live_df.empty:
    st.dataframe(live_df)
else:
    st.write("No live games available.")

# Display Upcoming NBA Games
st.subheader("Upcoming NBA Games")
if not upcoming_df.empty:
    st.dataframe(upcoming_df)
else:
    st.write("No upcoming games available.")

# Display NBA Game Data
st.subheader("NBA Game Data")
if not df.empty:
    st.dataframe(df)
else:
    st.write("No game data available.")
