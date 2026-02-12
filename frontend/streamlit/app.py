# frontend/streamlit/app.py
# Force rebuild - v2
import streamlit as st
import plotly.express as px  
import folium                
import pandas as pd          
import requests
import plotly.graph_objects as go
from streamlit_folium import st_folium
import folium
from datetime import datetime, timedelta

# Configuration
API_URL = "https://your-backend-url.com/api/v1"  # Update after deployment
st.set_page_config(
    page_title="NeerChitra | Tamil Nadu Water Intelligence",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #0ea5e9;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .stAlert {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/water.png", width=80)
        st.title("NeerChitra")
        st.caption("AI-Powered Water Body Intelligence")
        
        page = st.radio("Navigation", [
            "🏠 Dashboard",
            "🗺️ Live Map",
            "🔍 Water Body Analysis",
            "📊 Analytics",
            "⚙️ Settings"
        ])
        
        st.divider()
        st.caption("© 2024 Tamil Nadu Water Board")
    
    # Main content
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🗺️ Live Map":
        show_map()
    elif page == "🔍 Water Body Analysis":
        show_analysis()
    elif page == "📊 Analytics":
        show_analytics()

def show_dashboard():
    st.markdown('<p class="main-header">Tamil Nadu Water Intelligence Dashboard</p>', unsafe_allow_html=True)
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Water Bodies", "41,127", "+2 this month")
    with col2:
        st.metric("Critical Alerts", "12", "-3 from last week", delta_color="inverse")
    with col3:
        st.metric("Active Restorations", "15", "+2 this month")
    with col4:
        st.metric("Health Trend", "+2.3%", "YoY improvement")
    
    # Alert ticker
    st.subheader("🚨 Priority Alerts")
    alerts = [
        {"type": "critical", "msg": "Chembarambakkam Lake: 15% encroachment detected", "time": "2h ago"},
        {"type": "high", "msg": "Puzhal Lake: Industrial pollution alert", "time": "5h ago"},
        {"type": "warning", "msg": "Cyclone Michaung flood risk: 3 water bodies", "time": "1d ago"}
    ]
    
    for alert in alerts:
        if alert["type"] == "critical":
            st.error(f"🔴 {alert['msg']} • {alert['time']}")
        elif alert["type"] == "high":
            st.warning(f"🟡 {alert['msg']} • {alert['time']}")
        else:
            st.info(f"🔵 {alert['msg']} • {alert['time']}")
    
    # Split view: Map + Table
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("Live Situation Map")
        m = folium.Map(location=[11.1271, 78.6569], zoom_start=7)
        
        # Add markers for critical water bodies
        critical_bodies = [
            {"name": "Chembarambakkam Lake", "lat": 13.089, "lon": 80.058, "status": "critical"},
            {"name": "Puzhal Lake", "lat": 13.155, "lon": 80.204, "status": "degraded"},
            {"name": "Chitlapakkam Lake", "lat": 12.924, "lon": 80.133, "status": "healthy"}
        ]
        
        for wb in critical_bodies:
            color = "red" if wb["status"] == "critical" else "orange" if wb["status"] == "degraded" else "green"
            folium.Marker(
                [wb["lat"], wb["lon"]],
                popup=f"<b>{wb['name']}</b><br>Status: {wb['status']}",
                icon=folium.Icon(color=color, icon="tint", prefix="fa")
            ).add_to(m)
        
        st_folium(m, width=700, height=500)
    
    with col_right:
        st.subheader("Priority Restoration Queue")
        
        priority_data = pd.DataFrame([
            {"Rank": 1, "Water Body": "Chembarambakkam", "Score": 94, "Action": "Immediate"},
            {"Rank": 2, "Water Body": "Puzhal Lake", "Score": 87, "Action": "Urgent"},
            {"Rank": 3, "Water Body": "Madipakkam", "Score": 82, "Action": "High"},
            {"Rank": 4, "Water Body": "Velachery", "Score": 78, "Action": "High"},
            {"Rank": 5, "Water Body": "Muttukadu", "Score": 71, "Action": "Medium"}
        ])
        
        st.dataframe(
            priority_data,
            column_config={
                "Score": st.column_config.ProgressColumn(
                    "Risk Score",
                    help="Higher is more critical",
                    format="%d",
                    min_value=0,
                    max_value=100
                )
            },
            hide_index=True,
            use_container_width=True
        )

def show_analysis():
    st.header("🔍 Water Body Intelligence Analysis")
    
    # Water body selector
    water_body = st.selectbox(
        "Select Water Body",
        ["Chembarambakkam Lake", "Puzhal Lake", "Chitlapakkam Lake", "Madipakkam Lake"]
    )
    
    if water_body:
        # Fetch data from backend
        try:
            response = requests.post(f"{API_URL}/satellite/timeseries", json={
                "lat": 13.089,
                "lon": 80.058,
                "start_date": "2019-01-01",
                "end_date": "2024-12-31"
            })
            data = response.json()
            
            # Satellite comparison
            st.subheader("Satellite Evidence: 2019 vs 2024")
            
            col1, col2 = st.columns(2)
            with col1:
                st.image("https://via.placeholder.com/400x300/3b82f6/ffffff?text=2019+Satellite", 
                        caption="June 2019 - Baseline (Healthy)")
            with col2:
                st.image("https://via.placeholder.com/400x300/92400e/ffffff?text=2024+Satellite", 
                        caption="June 2024 - Current (Degraded)")
            
            # NDWI Time Series
            st.subheader("NDWI Health Trend (2019-2024)")
            
            if data.get("success"):
                df = pd.DataFrame(data["data"]["time_series"])
                df["date"] = pd.to_datetime(df["date"])
                
                fig = px.line(df, x="date", y="ndwi", 
                             title="Water Index Over Time",
                             labels={"ndwi": "NDWI Score", "date": "Date"})
                fig.add_hline(y=0, line_dash="dash", line_color="red", 
                             annotation_text="Water/Non-water threshold")
                st.plotly_chart(fig, use_container_width=True)
                
                # AI Insights
                st.info(f"""
                🤖 **AI Analysis**
                - Trend: {data['data']['statistics']['trend_direction']}
                - Anomalies detected: {data['data']['statistics']['anomaly_count']}
                - Confidence: 94%
                - Recommendation: Immediate boundary survey recommended
                """)
            
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            st.info("Using demo data...")
            
            # Demo data fallback
            dates = pd.date_range("2019-01-01", "2024-12-31", freq="M")
            ndwi_values = [0.4 - (i * 0.005) + (0.1 * (i % 12 == 6)) for i in range(len(dates))]
            
            demo_df = pd.DataFrame({"date": dates, "ndwi": ndwi_values})
            
            fig = px.line(demo_df, x="date", y="ndwi", 
                         title="Demo: NDWI Trend (Chembarambakkam Lake)")
            st.plotly_chart(fig, use_container_width=True)

def show_map():
    st.header("🗺️ Tamil Nadu Water Body Map")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        district = st.selectbox("District", ["All", "Chennai", "Kanchipuram", "Tiruvallur"])
    with col2:
        status = st.selectbox("Status", ["All", "Healthy", "Degraded", "Critical"])
    with col3:
        wb_type = st.selectbox("Type", ["All", "Lake", "River", "Tank", "Reservoir"])
    
    # Full screen map
    m = folium.Map(location=[11.1271, 78.6569], zoom_start=8, 
                   tiles="CartoDB positron")
    
    # Add heatmap layer for critical areas
    heat_data = [[13.089, 80.058, 0.9], [13.155, 80.204, 0.7], 
                 [12.924, 80.133, 0.3], [13.0, 80.2, 0.8]]
    
    from folium.plugins import HeatMap
    HeatMap(heat_data, radius=25).add_to(m)
    
    st_folium(m, width=1200, height=700)

def show_analytics():
    st.header("📊 State-wide Analytics")
    
    # District comparison
    districts = ["Chennai", "Kanchipuram", "Tiruvallur", "Cuddalore", "Villupuram"]
    health_scores = [65, 72, 58, 81, 69]
    
    fig = px.bar(x=districts, y=health_scores, 
                 labels={"x": "District", "y": "Avg Health Score"},
                 title="Water Body Health by District",
                 color=health_scores,
                 color_continuous_scale=["red", "yellow", "green"])
    st.plotly_chart(fig, use_container_width=True)
    
    # Restoration ROI
    st.subheader("Restoration ROI Analysis")
    roi_data = pd.DataFrame({
        "Project": ["Chembarambakkam", "Puzhal", "Chitlapakkam", "Madipakkam"],
        "Investment (Cr)": [12.5, 8.3, 3.2, 2.1],
        "Health Improvement": [25, 18, 32, 15]
    })
    
    fig2 = px.scatter(roi_data, x="Investment (Cr)", y="Health Improvement",
                     size="Investment (Cr)", text="Project",
                     title="Investment vs Impact")
    st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    main()
