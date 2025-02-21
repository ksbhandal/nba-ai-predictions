import os
import json
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta
import pytz

# Ensure required packages are installed (ideally, install these beforehand)
os.system("pip install requests pandas streamlit plotly pytz")

# API Configuration
API_KEY = "625a97bbcdb946c45a09a2dbddbdf0ce"  # API-Sports API Key
BASE_URL = "https://v1.basketball.api-sports.io/"
HEADERS = {
    "x-apisports-key": API_KEY,
    "Accept": "application/json"
}
DATA_FILE = "nba_data.json"
MAX_REQUESTS_PER_DAY = 90  # Keeping a buffer from the 100 limit

# Available free seasons (2021-2023)
AVAILABLE_SEASONS = ["2023", "2022", "2021"]
current_season = AVAILABLE_SEASONS[0]

# Function to fetch API data with improved logging
def fetch_api_data(endpoint, params=None):
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code != 200:
            st.error(f"Error {response.status_code}: {response.text}")
            return []
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

# Functions to load and save cached data
def load_saved_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading cache: {e}")
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# Check if we need to update (or if cache is empty)
def needs_update():
    saved_data = load_saved_data()
    last_update = saved_data.get("last_update")
    if last_update:
        try:
            last_update_time = datetime.strptime(last_update, "%Y-%m-%d %H:%M")
            if datetime.now() - last_update_time < timedelta(minutes=30):
                return False
        except Exception as e:
            st.error(f"Time parsing error: {e}")
    return True

# Load saved data
saved_data = load_saved_data()

# Force refresh if button clicked, cache is empty, or data is stale
if st.button("Refresh Data") or needs_update() or not saved_data:
    st.write("Fetching new data...")
    
    games_data = fetch_api_data("games", {"league": "12", "season": current_season})
    live_games_data = fetch_api_data("games", {"league": "12", "season": current_season, "live": "all"})
    upcoming_games_data = fetch_api_data("games", {"league": "12", "season": current_season, "date": datetime.now().date().isoformat()})
    player_stats_data = fetch_api_data("players/statistics", {"league": "12", "season": current_season})
    
    if not (games_data or live_games_data or upcoming_games_data):
        st.error("No data received from API. Please check your API key, season restrictions, or request limits.")
    else:
        st.success("Data successfully fetched!")
    
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

# Note: The last_update timestamp is saved in local time, so PST conversion may be off.
try:
    utc_time = datetime.strptime(saved_data.get("last_update", "2025-01-01 00:00"), "%Y-%m-%d %H:%M")
    pst_timezone = pytz.timezone("America/Los_Angeles")
    pst_time = utc_time.astimezone(pst_timezone)
except Exception:
    pst_time = datetime.now()

# Streamlit Dashboard
st.title("NBA AI Prediction Dashboard")
st.metric(label="Last Updated (PST)", value=pst_time.strftime("%Y-%m-%d %H:%M"))

st.subheader("Live NBA
