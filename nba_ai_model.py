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

# Step 1: Fetch NBA Data (Current Season)
current_season = datetime.datetime.now().year
NBA_API_URL = "https://www.balldontlie.io/api/v1/games"
params = {"seasons": [current_season], "per_page": 100}
response = requests.get(NBA_API_URL, params=params)
data = response.json()["data"]

# Convert to DataFrame
df = pd.DataFrame(data)

# Fetch Real-Time NBA Data
LIVE_NBA_API_URL = "https://www.balldontlie.io/api/v1/games/today"
live_response = requests.get(LIVE_NBA_API_URL)
live_data = live_response.json()["data"]
live_df = pd.DataFrame(live_data)

# Fetch Player Stats
PLAYER_STATS_API = "https://www.balldontlie.io/api/v1/stats"
player_response = requests.get(PLAYER_STATS_API, params={"seasons": [current_season], "per_page": 100})
player_data = player_response.json()["data"]
player_df = pd.DataFrame(player_data)

# Fetch Betting Odds
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
odds_params = {"regions": "us", "markets": "h2h,spreads,totals", "apiKey": "YOUR_API_KEY"}
odds_response = requests.get(ODDS_API_URL, params=odds_params)
odds_data = odds_response.json()
odds_df = pd.DataFrame(odds_data)

# Step 2: Feature Engineering (Extract relevant stats)
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

# Update Momentum and Clutch Performance Metrics to Last 15 Games
df["home_last_15_avg"] = df["home_team_score"].rolling(window=15).mean()
df["visitor_last_15_avg"] = df["visitor_team_score"].rolling(window=15).mean()
df["clutch_performance"] = (df["home_team_score"] - df["visitor_team_score"]).abs() / df["point_diff"]

# Compare AI Predictions with Betting Odds
odds_df = odds_df.explode("bookmakers")
odds_df = odds_df.reset_index()

# Function to Send Alerts for High-Value Bets
def send_email_alert(subject, body, recipient_email):
    sender_email = "your_email@example.com"
    sender_password = "your_password"
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    with smtplib.SMTP('smtp.example.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())

# Streamlit Dashboard
st.title("NBA AI Prediction Dashboard")
st.metric(label="Optimized Model Accuracy", value="N/A")

# Display Real-Time Games Data
st.subheader("Live NBA Games")
if not live_df.empty:
    st.dataframe(live_df[["home_team.full_name", "visitor_team.full_name", "home_team_score", "visitor_team_score"]])
else:
    st.write("No live games available.")
