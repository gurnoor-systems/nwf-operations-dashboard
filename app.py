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
# ==========================================
# 2. DATABASE CONNECTIONS & CACHED INGESTION
# ==========================================

ATTENDANCE_URL = "https://docs.google.com/spreadsheets/d/1FN3dwVcuEyTwjoQTsyY-ABKmXEQKk5CBsLs6dLXaAVQ/edit"
# Add your 01_nwf_volunteerdirectory URL here:
DIRECTORY_URL = "https://docs.google.com/spreadsheets/d/19X1b-B2nL5u02vhqxNAEcvdY9J_URo2lG1oTii58Mc0/edit"

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def load_strike_summary():
    return conn.read(spreadsheet=ATTENDANCE_URL, worksheet="Strike_Summary")

@st.cache_data(ttl=300)
def load_directory():
    # Make sure "Sheet1" matches the exact tab name at the bottom of your directory file
    return conn.read(spreadsheet=DIRECTORY_URL, worksheet="Volunteer_Directory")

try:
    # 1. Load the Strike Data
    df_master = load_strike_summary()
    df_master = df_master[~df_master["Department"].str.contains("Void", case=False, na=False)]
    
    # 2. Load the Directory Data
    df_dir = load_directory()
    
    # 3. Privacy Filter: Keep ONLY the Volunteer ID and Email (Drop Phone Numbers)
    # Note: If your email column is named differently (e.g., "Email Address"), update it below
    df_dir_clean = df_dir[["Volunteer ID", "Contact (Email)"]] 
    
    # 4. The Merge: Join the clean directory to the strike summary
    df_master = pd.merge(df_master, df_dir_clean, on="Volunteer ID", how="left")
    
    # 5. Clean Data Types for Math
    df_master["Total_Strikes"] = pd.to_numeric(df_master["Total_Strikes"], errors="coerce").fillna(0)
    df_master["Total_Events"] = pd.to_numeric(df_master["Total_Events"], errors="coerce").fillna(0)
    df_master["Present"] = pd.to_numeric(df_master["Present"], errors="coerce").fillna(0)
    
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
    total_volunteers = len(df_master)
    good_standing_count = len(df_master[df_master["SOP_Status"] == "GOOD STANDING"])
    good_standing_pct = (good_standing_count / total_volunteers * 100) if total_volunteers > 0 else 0
    total_events_logged = int(df_master["Total_Events"].sum())
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Active Roster", f"{total_volunteers} Members")
    col2.metric("Good Standing Rate", f"{good_standing_pct:.1f}%")
    col3.metric("Total Drive Logs", f"{total_events_logged} Logs")
    col4.metric("Active Departments", f"{df_master['Department'].nunique()}")
    
    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.write("### Roster Breakdown by Department")
        dept_counts = df_master["Department"].value_counts()
        st.bar_chart(dept_counts)
        
    with col_chart2:
        st.write("### Standing Status Distribution")
        status_counts = df_master["SOP_Status"].value_counts()
        st.bar_chart(status_counts)

# ------------------------------------------
# TAB 2: DEPARTMENT OPERATIONS (FILTERED)
# ------------------------------------------
with tab_dept:
    st.subheader("Departmental Roster Explorer")
    st.write("Department Heads can filter below to isolate and manage their specific team members.")
    
    # Get list of unique departments
    departments = ["All Departments"] + list(df_master["Department"].unique())
    selected_dept = st.selectbox("Select Department:", departments)
    
    # Filter DataFrame based on selection
    if selected_dept == "All Departments":
        df_filtered = df_master
    else:
        df_filtered = df_master[df_master["Department"] == selected_dept]
        
    st.write(f"Showing **{len(df_filtered)}** team members in **{selected_dept}**:")
    
    # Render interactive, clean dataframe
    st.dataframe(
        df_filtered[["Volunteer ID", "Full_Name","Contact (Email)", "Department", "Total_Events", "Present", "Attendance_Rate", "SOP_Status"]],
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
        df_warnings = df_master[df_master["Total_Strikes"] > 0].sort_values(by="Total_Strikes", ascending=False)
        
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
        df_eligible = df_master[df_master["SOP_Status"] == "GOOD STANDING"]
        st.dataframe(
            df_eligible[["Volunteer ID", "Full_Name", "Department", "Attendance_Rate"]],
            use_container_width=True,
            hide_index=True
        )