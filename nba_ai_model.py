import os
import json
import requests
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta
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
MAX_REQUESTS_PER_DAY = 7500  # Adjusted for Pro Plan

# Use latest available season
current_season = "2024-2025"  # Updated for latest season

# Function to fetch API data
def fetch_api_data(endpoint, params=None):
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        if "response" in data:
            if not data["response"]:
                st.warning(f"No data returned for {endpoint}. Params: {params}")
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
        if datetime.now() - last_update_time < timedelta(minutes=15):  # Update every 15 minutes
            return False
    return True

# Load saved data
saved_data = load_saved_data()

# Refresh Button
if st.button("Refresh Data") or needs_update():
    st.write("Fetching new data...")
    
    # Fetch latest season data
    games_data = fetch_api_data("games", {"league": "12", "season": current_season})
    live_games_data = fetch_api_data("games", {"league": "12", "season": current_season, "live": "all"})
    upcoming_games_data = fetch_api_data("games", {"league": "12", "season": current_season, "date": (datetime.now().date()).isoformat()})
    player_stats_data = fetch_api_data("players/statistics", {"league": "12", "season": current_season})
    
    # Validate API response
    if not games_data and not live_games_data and not upcoming_games_data:
        st.error("No data received from API. Please check your API key, season restrictions, or request limits.")
    else:
        st.success("Data successfully fetched!")
    
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
utc_time = datetime.strptime(saved_data.get("last_update", "2025-01-01 00:00"), "%Y-%m-%d %H:%M")
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
