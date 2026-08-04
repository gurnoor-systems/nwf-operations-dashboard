import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="NWF Executive Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("🛡️ Naunidh Welfare Foundation — Operations & Analytics Engine")
st.caption("Live Operational Intelligence & Executive Impact Portal")
st.markdown("---")

# ==========================================
# 2. DATABASE CONNECTIONS & CACHED INGESTION
# ==========================================
# Google Sheet URLs (Add additional departmental URLs here as needed)
ATTENDANCE_URL = "https://docs.google.com/spreadsheets/d/1FN3dwVcuEyTwjoQTsyY-ABKmXEQKk5CBsLs6dLXaAVQ/edit?gid=1238373230#gid=1238373230"

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)  # Caches data for 5 minutes for lightning-fast loads
def load_strike_summary():
    return conn.read(spreadsheet=ATTENDANCE_URL, worksheet="Strike_Summary")

try:
    df_strikes = load_strike_summary()
    
    # Ensure numeric types for calculations
    df_strikes["Total_Strikes"] = pd.to_numeric(df_strikes["Total_Strikes"], errors="coerce").fillna(0)
    df_strikes["Total_Events"] = pd.to_numeric(df_strikes["Total_Events"], errors="coerce").fillna(0)
    df_strikes["Present"] = pd.to_numeric(df_strikes["Present"], errors="coerce").fillna(0)
    
except Exception as e:
    st.error(f"Failed to load database: {e}")
    st.stop()

# ==========================================
# 3. DASHBOARD TABS
# ==========================================
tab_exec, tab_dept, tab_hr = st.tabs([
    "📈 Executive Pitch & Overview", 
    "👥 Department Operations", 
    "⚠️ HR & Strike Monitor"
])

# ------------------------------------------
# TAB 1: EXECUTIVE PITCH & OVERVIEW
# ------------------------------------------
with tab_exec:
    st.subheader("Key Organizational Indicators (KPIs)")
    
    # Calculate live metrics
    total_volunteers = len(df_strikes)
    good_standing_count = len(df_strikes[df_strikes["SOP_Status"] == "GOOD STANDING"])
    good_standing_pct = (good_standing_count / total_volunteers * 100) if total_volunteers > 0 else 0
    total_events_logged = int(df_strikes["Total_Events"].sum())
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Active Roster", f"{total_volunteers} Members")
    col2.metric("Good Standing Rate", f"{good_standing_pct:.1f}%")
    col3.metric("Total Drive Logs", f"{total_events_logged} Logs")
    col4.metric("Active Departments", f"{df_strikes['Department'].nunique()}")
    
    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.write("### Roster Breakdown by Department")
        dept_counts = df_strikes["Department"].value_counts()
        st.bar_chart(dept_counts)
        
    with col_chart2:
        st.write("### Standing Status Distribution")
        status_counts = df_strikes["SOP_Status"].value_counts()
        st.bar_chart(status_counts)

# ------------------------------------------
# TAB 2: DEPARTMENT OPERATIONS (FILTERED)
# ------------------------------------------
with tab_dept:
    st.subheader("Departmental Roster Explorer")
    st.write("Department Heads can filter below to isolate and manage their specific team members.")
    
    # Get list of unique departments
    departments = ["All Departments"] + list(df_strikes["Department"].unique())
    selected_dept = st.selectbox("Select Department:", departments)
    
    # Filter DataFrame based on selection
    if selected_dept == "All Departments":
        df_filtered = df_strikes
    else:
        df_filtered = df_strikes[df_strikes["Department"] == selected_dept]
        
    st.write(f"Showing **{len(df_filtered)}** team members in **{selected_dept}**:")
    
    # Render interactive, clean dataframe
    st.dataframe(
        df_filtered[["Volunteer ID", "Full_Name", "Department", "Total_Events", "Present", "Attendance_Rate", "SOP_Status"]],
        use_container_width=True,
        hide_index=True
    )

# ------------------------------------------
# TAB 3: HR & STRIKE MONITOR
# ------------------------------------------
with tab_hr:
    st.subheader("Compliance & Certificate Oversight")
    
    col_hr1, col_hr2 = st.columns(2)
    
    with col_hr1:
        st.write("### 🚨 High Risk / Warning List (Strikes ≥ 1)")
        df_warnings = df_strikes[df_strikes["Total_Strikes"] > 0].sort_values(by="Total_Strikes", ascending=False)
        
        if len(df_warnings) > 0:
            st.dataframe(
                df_warnings[["Volunteer ID", "Full_Name", "Department", "Total_Strikes", "SOP_Status"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("No active strikes logged across the foundation!")
            
    with col_hr2:
        st.write("### 🎓 Certificate Eligible (Good Standing)")
        df_eligible = df_strikes[df_strikes["SOP_Status"] == "GOOD STANDING"]
        st.dataframe(
            df_eligible[["Volunteer ID", "Full_Name", "Department", "Attendance_Rate"]],
            use_container_width=True,
            hide_index=True
        )