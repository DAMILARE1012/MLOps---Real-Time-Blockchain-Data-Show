import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
import matplotlib.pyplot as plt
import time
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configure page
st.set_page_config(
    page_title="Blockchain Anomaly Detection", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Cache data loading functions
@st.cache_data(ttl=30)  # Cache for 30 seconds
def load_anomaly_data():
    """Load and cache anomaly events data"""
    try:
        if os.path.exists("anomaly_events.csv"):
            # Check if file has data beyond header
            with open("anomaly_events.csv", 'r') as f:
                lines = f.readlines()
                if len(lines) <= 1:  # Only header or empty
                    return pd.DataFrame(columns=['hash', 'score', 'total_value', 'fee', 'input_count', 'output_count', 'address', 'timestamp'])
            
            df = pd.read_csv("anomaly_events.csv")
            if df.empty:
                return pd.DataFrame(columns=['hash', 'score', 'total_value', 'fee', 'input_count', 'output_count', 'address', 'timestamp'])
            
            # Convert timestamp if needed
            if 'timestamp' not in df.columns and not df.empty:
                df['timestamp'] = pd.to_datetime(df['hash'].apply(lambda x: int(x[:8], 16)), unit='s', errors='coerce')
            return df
        return pd.DataFrame(columns=['hash', 'score', 'total_value', 'fee', 'input_count', 'output_count', 'address', 'timestamp'])
    except Exception as e:
        st.error(f"Error loading anomaly data: {e}")
        return pd.DataFrame(columns=['hash', 'score', 'total_value', 'fee', 'input_count', 'output_count', 'address', 'timestamp'])

@st.cache_data(ttl=30)  # Cache for 30 seconds
def load_whale_data():
    """Load and cache whale events data"""
    try:
        if os.path.exists("whale_events.csv"):
            # Check if file has data beyond header
            with open("whale_events.csv", 'r') as f:
                lines = f.readlines()
                if len(lines) <= 1:  # Only header or empty
                    return pd.DataFrame(columns=['hash', 'total_value_btc', 'fee', 'input_count', 'output_count', 'address', 'timestamp'])
            
            df = pd.read_csv("whale_events.csv")
            if df.empty:
                return pd.DataFrame(columns=['hash', 'total_value_btc', 'fee', 'input_count', 'output_count', 'address', 'timestamp'])
            
            # Convert timestamp if needed
            if 'timestamp' not in df.columns and not df.empty:
                df['timestamp'] = pd.to_datetime(df['hash'].apply(lambda x: int(x[:8], 16)), unit='s', errors='coerce')
            return df
        return pd.DataFrame(columns=['hash', 'total_value_btc', 'fee', 'input_count', 'output_count', 'address', 'timestamp'])
    except Exception as e:
        st.error(f"Error loading whale data: {e}")
        return pd.DataFrame(columns=['hash', 'total_value_btc', 'fee', 'input_count', 'output_count', 'address', 'timestamp'])

@st.cache_data(ttl=60)  # Cache for 1 minute
def load_risk_data():
    """Load and cache risk scoring data"""
    try:
        if os.path.exists("address_risk_scores.csv"):
            return pd.read_csv("address_risk_scores.csv")
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

# Dashboard header
st.title("🔍 Real-Time Blockchain Anomaly Detection Dashboard")

# Sidebar controls
st.sidebar.header("⚙️ Controls")
auto_refresh = st.sidebar.toggle("Auto-refresh", value=False)
refresh_interval = st.sidebar.slider("Refresh interval (seconds)", 5, 60, 30)

if st.sidebar.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()

# Load data
anomaly_df = load_anomaly_data()
whale_df = load_whale_data()
risk_df = load_risk_data()

# Main metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Anomalies", len(anomaly_df))
    
with col2:
    st.metric("Total Whales", len(whale_df))
    
with col3:
    recent_anomalies = len(anomaly_df[anomaly_df['timestamp'] > datetime.now() - pd.Timedelta(hours=1)]) if not anomaly_df.empty else 0
    st.metric("Anomalies (1h)", recent_anomalies)
    
with col4:
    system_status = "🟢 Active" if os.path.exists("data_pipeline.log") else "🔴 Inactive"
    st.metric("System Status", system_status)

# Show last update time
if not anomaly_df.empty:
    last_update = anomaly_df['timestamp'].max() if 'timestamp' in anomaly_df.columns else "Unknown"
    st.info(f"📅 Last update: {last_update}")

# Tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🚨 Anomalies", "🐋 Whales", "🏆 Risk Analysis"])

with tab1:
    st.header("📊 System Overview")
    
    # Real-time charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Anomaly Rate Over Time")
        if not anomaly_df.empty and 'timestamp' in anomaly_df.columns:
            # Use plotly for better performance
            hourly_anomalies = anomaly_df.set_index('timestamp').resample('1H').size()
            fig = px.line(x=hourly_anomalies.index, y=hourly_anomalies.values, 
                         labels={'x': 'Time', 'y': 'Anomalies per Hour'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No anomaly data available")
    
    with col2:
        st.subheader("Whale Activity")
        if not whale_df.empty and 'timestamp' in whale_df.columns:
            hourly_whales = whale_df.set_index('timestamp').resample('1H').size()
            fig = px.line(x=hourly_whales.index, y=hourly_whales.values, 
                         labels={'x': 'Time', 'y': 'Whales per Hour'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No whale data available")

with tab2:
    st.header("🚨 Anomaly Detection")
    
    if not anomaly_df.empty:
        # Anomaly score distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Score Distribution")
            fig = px.histogram(anomaly_df, x='score', nbins=30, 
                             title="Distribution of Anomaly Scores")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Top Anomalous Addresses")
            if 'address' in anomaly_df.columns:
                top_addresses = anomaly_df['address'].value_counts().head(10)
                fig = px.bar(x=top_addresses.index, y=top_addresses.values,
                           labels={'x': 'Address', 'y': 'Anomaly Count'})
                st.plotly_chart(fig, use_container_width=True)
        
        # Interactive anomaly threshold
        st.subheader("🎚️ Anomaly Threshold Filter")
        min_score = float(anomaly_df['score'].min())
        max_score = float(anomaly_df['score'].max())
        threshold = st.slider("Anomaly Score Threshold", min_score, max_score, min_score, step=0.01)
        
        filtered_anomalies = anomaly_df[anomaly_df['score'] <= threshold]
        st.write(f"Showing {len(filtered_anomalies)} anomalies below threshold")
        
        # Paginated results
        page_size = 20
        total_pages = (len(filtered_anomalies) + page_size - 1) // page_size
        page = st.selectbox("Page", range(1, total_pages + 1)) if total_pages > 0 else 1
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        st.dataframe(
            filtered_anomalies.iloc[start_idx:end_idx].sort_values('timestamp', ascending=False),
            use_container_width=True
        )
    else:
        st.warning("No anomaly data available")

with tab3:
    st.header("🐋 Whale Tracker")
    
    if not whale_df.empty:
        # Whale metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_whale_value = whale_df['total_value_btc'].mean()
            st.metric("Average Whale Value", f"{avg_whale_value:.2f} BTC")
        
        with col2:
            max_whale_value = whale_df['total_value_btc'].max()
            st.metric("Largest Whale", f"{max_whale_value:.2f} BTC")
        
        with col3:
            total_whale_volume = whale_df['total_value_btc'].sum()
            st.metric("Total Whale Volume", f"{total_whale_volume:.2f} BTC")
        
        # Whale value distribution
        st.subheader("Whale Value Distribution")
        fig = px.histogram(whale_df, x='total_value_btc', nbins=50,
                         title="Distribution of Whale Transaction Values")
        st.plotly_chart(fig, use_container_width=True)
        
        # Recent whales
        st.subheader("Recent Whale Transactions")
        recent_whales = whale_df.sort_values('timestamp', ascending=False).head(20)
        st.dataframe(recent_whales, use_container_width=True)
        
        # Top whale addresses
        if 'address' in whale_df.columns:
            st.subheader("Top Whale Addresses")
            top_whale_addresses = whale_df['address'].value_counts().head(10)
            fig = px.bar(x=top_whale_addresses.index, y=top_whale_addresses.values,
                       labels={'x': 'Address', 'y': 'Transaction Count'})
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No whale data available")

with tab4:
    st.header("🏆 Risk Analysis")
    
    if not risk_df.empty:
        st.subheader("Top Risky Addresses")
        st.dataframe(risk_df.head(10), use_container_width=True)
        
        # Address selection
        selected_address = st.selectbox("Select address to analyze:", risk_df.index.astype(str))
        
        if selected_address:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Anomalies for this address")
                if not anomaly_df.empty and 'address' in anomaly_df.columns:
                    address_anomalies = anomaly_df[anomaly_df['address'] == selected_address]
                    st.dataframe(address_anomalies.tail(10), use_container_width=True)
                else:
                    st.info("No anomaly data for this address")
            
            with col2:
                st.subheader("Whale transactions for this address")
                if not whale_df.empty and 'address' in whale_df.columns:
                    address_whales = whale_df[whale_df['address'] == selected_address]
                    st.dataframe(address_whales.tail(10), use_container_width=True)
                else:
                    st.info("No whale data for this address")
    else:
        st.warning("No risk analysis data available")

# System health section
st.header("🔧 System Health")

col1, col2, col3 = st.columns(3)

with col1:
    model_exists = os.path.exists("models/anomaly_model.pkl")
    st.metric("ML Model", "✅ Loaded" if model_exists else "❌ Missing")

with col2:
    pipeline_running = os.path.exists("data_pipeline.log")
    st.metric("Data Pipeline", "✅ Running" if pipeline_running else "❌ Stopped")

with col3:
    if pipeline_running:
        last_log_update = datetime.fromtimestamp(os.path.getmtime("data_pipeline.log"))
        time_diff = datetime.now() - last_log_update
        status = "✅ Active" if time_diff.seconds < 60 else "⚠️ Stale"
        st.metric("Pipeline Status", status)

# Auto-refresh logic (non-blocking)
if auto_refresh:
    # Use JavaScript to refresh page after interval
    st.markdown(f"""
    <script>
    setTimeout(function(){{
        window.location.reload();
    }}, {refresh_interval * 1000});
    </script>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("🚀 **Blockchain Anomaly Detection System** | Real-time monitoring and alerts")