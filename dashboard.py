import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
import matplotlib.pyplot as plt
import shap
import time

st.set_page_config(page_title="Blockchain Anomaly Detection", layout="wide", initial_sidebar_state="expanded")

st.title("Real-Time Blockchain Anomaly Detection Dashboard")

# Add auto-refresh functionality
refresh_interval = st.sidebar.slider("Auto-refresh interval (seconds)", 5, 60, 30)
if st.sidebar.button("Refresh Now"):
    st.rerun()

# Auto-refresh placeholder
placeholder = st.empty()
auto_refresh = st.sidebar.checkbox("Enable auto-refresh", value=True)

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()

# Load anomaly events
try:
    df = pd.read_csv("anomaly_events.csv")
    st.write(f"Total anomalies detected: {len(df)}")

    # 1. Anomaly Rate Over Time (per hour)
    st.subheader("Anomaly Rate Over Time (per hour)")
    if 'timestamp' not in df.columns:
        df['timestamp'] = pd.to_datetime(df['hash'].apply(lambda x: int(x[:8], 16)), unit='s', errors='coerce')
    df_time = df.dropna(subset=['timestamp']).set_index('timestamp')
    anomaly_rate = df_time.resample('1h').size()
    st.line_chart(anomaly_rate)

    # 2. Top Addresses Involved in Anomalies (if available)
    st.subheader("Top Addresses in Anomalies")
    if 'address' in df.columns:
        top_addresses = df['address'].value_counts().head(10)
        st.bar_chart(top_addresses)
    else:
        st.info("Address data not available in anomaly log.")

    # 3. Distribution of Transaction Values (Anomalies) - FIXED
    st.subheader("Distribution of Transaction Values (Anomalies)")
    fig, ax = plt.subplots()
    ax.hist(df['total_value'], bins=30)
    ax.set_xlabel('Total Value')
    ax.set_ylabel('Frequency')
    ax.set_title('Histogram of Total Transaction Value (Anomalies)')
    st.pyplot(fig)

    # 4. Recent Alerts Table
    st.subheader("Recent Anomaly Alerts")
    st.dataframe(df.sort_values('timestamp', ascending=False).head(20))

    # 5. Anomaly Score Threshold Slider
    st.subheader("Adjust Anomaly Score Threshold")
    min_score = float(df['score'].min())
    max_score = float(df['score'].max())
    threshold = st.slider("Anomaly Score Threshold", min_value=min_score, max_value=max_score, value=min_score, step=0.01)
    filtered = df[df['score'] <= threshold]
    st.write(f"Number of anomalies below threshold: {len(filtered)}")
    st.dataframe(filtered.head(20))

    # 6. System Health/Status
    st.subheader("System Health/Status")
    model_exists = os.path.exists("models/anomaly_model.pkl")
    pipeline_running = os.path.exists("data_pipeline.log")
    st.write(f"Anomaly Model Loaded: {'✅' if model_exists else '❌'}")
    st.write(f"Pipeline Log File Present: {'✅' if pipeline_running else '❌'}")
    if pipeline_running:
        last_update = datetime.fromtimestamp(os.path.getmtime("data_pipeline.log"))
        st.write(f"Last Pipeline Log Update: {last_update}")

except FileNotFoundError:
    st.warning("No anomaly events file found. The system is starting up or no anomalies have been detected yet.")
except Exception as e:
    st.error(f"Error loading anomaly events: {e}")

# Show last update time
if os.path.exists("anomaly_events.csv"):
    last_update = datetime.fromtimestamp(os.path.getmtime("anomaly_events.csv"))
    st.info(f"Last updated: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")

st.write("This dashboard updates as new anomalies are detected in real time.")

st.header("🐋 Whale Tracker")
try:
    whale_df = pd.read_csv("whale_events.csv")
    st.write(f"Total whale transactions detected: {len(whale_df)}")
    # Whale rate over time
    if 'timestamp' not in whale_df.columns:
        whale_df['timestamp'] = pd.to_datetime(whale_df['hash'].apply(lambda x: int(x[:8], 16)), unit='s', errors='coerce')
    whale_rate = whale_df.dropna(subset=['timestamp']).set_index('timestamp').resample('1h').size()
    st.line_chart(whale_rate)
    # Recent whales
    st.subheader("Recent Whale Transactions")
    st.dataframe(whale_df.sort_values('timestamp', ascending=False).head(20))
    # Top whale addresses
    if 'address' in whale_df.columns:
        st.subheader("Top Whale Addresses")
        st.bar_chart(whale_df['address'].value_counts().head(10))
except FileNotFoundError:
    st.info("No whale transactions file found. The system is starting up or no whale transactions have been detected yet.")
except Exception as e:
    st.error(f"Error loading whale transactions: {e}")

# Address Risk Scoring Leaderboard
st.header("🏆 Address Risk Leaderboard")
try:
    risk_df = pd.read_csv("address_risk_scores.csv")
    st.write("Top Risky Addresses (based on anomaly & whale frequency):")
    st.dataframe(risk_df.head(10))
    selected_address = st.selectbox("Select address to view recent activity:", risk_df.index.astype(str))
    # Show recent anomalies/whales for this address
    anomaly_df = pd.read_csv("anomaly_events.csv") if os.path.exists("anomaly_events.csv") else pd.DataFrame()
    whale_df = pd.read_csv("whale_events.csv") if os.path.exists("whale_events.csv") else pd.DataFrame()
    st.write("Recent anomalies for this address:")
    st.dataframe(anomaly_df[anomaly_df['address'] == selected_address].tail(10))
    st.write("Recent whale transactions for this address:")
    st.dataframe(whale_df[whale_df['address'] == selected_address].tail(10))
except FileNotFoundError:
    st.info("No address risk data file found. The system is starting up or no risk data has been generated yet.")
except Exception as e:
    st.error(f"Error loading address risk data: {e}")

# Anomaly Explanation (SHAP)
st.header("🔍 Anomaly Explanation")
try:
    import joblib
    model = joblib.load("models/anomaly_model.pkl")
    features = pd.read_csv("historical_features.csv")
    explainer = shap.Explainer(model, features)
    anomaly_df = pd.read_csv("anomaly_events.csv")
    if not anomaly_df.empty:
        st.write("Select an anomaly to explain:")
        idx = st.selectbox("Anomaly index", anomaly_df.index)
        tx_features = anomaly_df.loc[idx, ['total_value', 'fee', 'input_count', 'output_count']].values.reshape(1, -1)
        shap_values = explainer(tx_features)
        st.write("Feature contributions to anomaly score:")
        st.pyplot(shap.plots.waterfall(shap_values[0], show=False))
except Exception as e:
    st.info(f"Anomaly explanation not available. ({e})")

# Real-Time Transaction Volume & Heatmaps
st.header("📊 Real-Time Transaction Volume & Heatmaps")
try:
    # Transaction volume by hour
    if 'timestamp' in anomaly_df.columns:
        volume_by_hour = anomaly_df.set_index('timestamp').resample('1h').size()
        st.subheader("Anomaly Transaction Volume by Hour")
        st.line_chart(volume_by_hour)
    # Heatmap: address vs. hour (if address available)
    if 'address' in anomaly_df.columns and 'timestamp' in anomaly_df.columns:
        anomaly_df['hour'] = pd.to_datetime(anomaly_df['timestamp']).dt.hour
        heatmap_data = pd.pivot_table(anomaly_df, index='address', columns='hour', aggfunc='size', fill_value=0)
        st.subheader("Anomaly Heatmap: Address vs. Hour")
        st.dataframe(heatmap_data)
except Exception as e:
    st.info(f"No real-time volume or heatmap data available. ({e})") 