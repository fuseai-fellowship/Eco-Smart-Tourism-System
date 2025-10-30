import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import plotly.graph_objects as go

# -------------------- CONFIG --------------------
API_URL = "http://127.0.0.1:8000/predict/"  # your FastAPI prediction endpoint
REFRESH_INTERVAL = 5  # seconds between API calls

st.set_page_config(page_title="Traveller Risk Analysis Dashboard", layout="wide")
st.title("🧭 Traveller Risk Analysis — Live Wearables Dashboard")

# -------------------- SESSION STATE --------------------
if "live_data" not in st.session_state:
    st.session_state.live_data = pd.DataFrame(columns=[
        "timestamp", "hr_bpm", "spo2_pct", "skin_temp", "blood_pressure", "altitude", "steps"
    ])

# -------------------- FUNCTION: Get data from API --------------------
def fetch_live_data():
    """Fetches data & prediction from FastAPI endpoint"""
    try:
        response = requests.get(API_URL, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Could not connect to API: {e}")
        return None

# -------------------- FUNCTION: Update chart data --------------------
def update_data(new_data):
    df = st.session_state.live_data
    row = {
        "timestamp": pd.Timestamp.now(),
        "hr_bpm": new_data.get("hr_bpm", np.nan),
        "spo2_pct": new_data.get("spo2_pct", np.nan),
        "skin_temp": new_data.get("skin_temp", np.nan),
        "blood_pressure": f"{new_data.get('bp_sys', '')}/{new_data.get('bp_dia', '')}",
        "altitude": new_data.get("altitude", np.nan),
        "steps": new_data.get("steps", np.nan),
    }
    st.session_state.live_data = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

# -------------------- LAYOUT --------------------
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📡 Live Metrics")
    live_placeholder = st.empty()
    st.divider()
    st.subheader("🩺 Recommendations")
    rec_placeholder = st.empty()

with col2:
    st.subheader("📈 Real-time Trends")
    chart_placeholder = st.empty()
    risk_placeholder = st.empty()

# -------------------- MAIN LOOP --------------------
st.markdown("### 🔁 Live Data Stream")
start_btn = st.button("▶️ Start Monitoring")
stop_btn = st.button("⏹ Stop")

if start_btn:
    st.session_state["run"] = True
if stop_btn:
    st.session_state["run"] = False

# -------------------- LIVE UPDATE LOOP --------------------
while st.session_state.get("run", False):
    data = fetch_live_data()

    if data:
        # Assume API returns something like:
        # {
        #   "hr_bpm": 90,
        #   "spo2_pct": 98.8,
        #   "skin_temp": 33.7,
        #   "bp_sys": 120,
        #   "bp_dia": 78,
        #   "altitude": 300,
        #   "steps": 10000,
        #   "predicted_risk_level": "Low"
        # }

        update_data(data)

        # Display live metrics
        live_placeholder.markdown(f"""
        **Heart Rate:** {data['hr_bpm']} bpm  
        **SpO₂:** {data['spo2_pct']} %  
        **Skin Temp:** {data['skin_temp']} °C  
        **Blood Pressure:** {data['bp_sys']}/{data['bp_dia']} mmHg  
        **Altitude:** {data['altitude']} m  
        **Steps:** {data['steps']}  
        **Predicted Risk:** 🟢 {data['predicted_risk_level'].upper()}  
        """)

        # Plot live metrics
        df = st.session_state.live_data.tail(30)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df["hr_bpm"], mode="lines+markers", name="Heart Rate"))
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df["spo2_pct"], mode="lines+markers", name="SpO₂"))
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df["skin_temp"], mode="lines+markers", name="Skin Temp"))
        fig.update_layout(
            title="Live Wearable Metrics",
            xaxis_title="Time",
            yaxis_title="Value",
            height=400,
            template="plotly_dark"
        )
        chart_placeholder.plotly_chart(fig, use_container_width=True)

        # Risk level indicator
        risk_level = data["predicted_risk_level"].lower()
        color_map = {"low": "🟢", "moderate": "🟡", "high": "🟠", "critical": "🔴"}
        risk_placeholder.markdown(f"### Current Risk Level: {color_map.get(risk_level, '⚪')} **{risk_level.upper()}**")

        # Recommendations
        if risk_level == "low":
            rec_placeholder.success("✅ Low risk — continue normal activities but monitor metrics.")
        elif risk_level == "moderate":
            rec_placeholder.warning("⚠️ Moderate risk — stay hydrated and avoid heavy exertion.")
        elif risk_level == "high":
            rec_placeholder.error("🚨 High risk — rest, hydrate, and seek assistance if symptoms persist.")
        elif risk_level == "critical":
            rec_placeholder.error("🆘 Critical risk — immediate medical attention required!")
        else:
            rec_placeholder.info("No data available.")

    time.sleep(REFRESH_INTERVAL)
