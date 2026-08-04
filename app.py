import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="NWF Executive Dashboard",
    page_icon="logo.png",
    layout="wide"
)

col_logo, col_title = st.columns([1, 11]) # The title column is 11x wider than the logo
with col_logo:
    st.image("logo.png", use_container_width=True)
with col_title:
    st.title("Naunidh Welfare Foundation — Analytical Dashboard")
    st.caption("Live Operational Intelligence & Executive Impact Portal")
st.divider()

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

# PLACEHOLDER: Paste your Drive_log URL here (remember to delete the ?gid= part!)
DRIVES_URL = "https://docs.google.com/spreadsheets/d/1wL81j3QWoHUO4_6AHA9BEnEhwzLe1KtHDIOceI446Og/edit"

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def load_strike_summary():
    return conn.read(spreadsheet=ATTENDANCE_URL, worksheet="Strike_Summary")

@st.cache_data(ttl=300)
def load_directory():

    return conn.read(spreadsheet=DIRECTORY_URL, worksheet="Volunteer_Directory")

@st.cache_data(ttl=300)
def load_drives_data():

    return conn.read(spreadsheet=DRIVES_URL, worksheet="Drive_log")

try:
# 1. Load the Strike Data
    df_master = load_strike_summary()
    df_master = df_master[~df_master["Department"].str.contains("Void", case=False, na=False)]
    
# 2. Load the Directory Data
    df_dir = load_directory()
    
    # 1. Privacy Filter: Keep ONLY the Volunteer ID and Email (Drop Phone Numbers)
    # Note: If your email column is named differently (e.g., "Email Address"), update it below
    df_dir_clean = df_dir[["Volunteer ID", "Contact (Email)"]] 
    
    # 2. The Merge: Joining the clean directory to the strike summary
    df_master = pd.merge(df_master, df_dir_clean, on="Volunteer ID", how="left")
    
    # 3. Clean Data Types
    df_master["Total_Strikes"] = pd.to_numeric(df_master["Total_Strikes"], errors="coerce").fillna(0)
    df_master["Total_Events"] = pd.to_numeric(df_master["Total_Events"], errors="coerce").fillna(0)
    df_master["Present"] = pd.to_numeric(df_master["Present"], errors="coerce").fillna(0)

# 3. Load Drives Impact Data
    df_drives = load_drives_data()
    
except Exception as e:
    st.error(f"Failed to load database: {e}")
    st.stop()

# ==========================================
# 3. DASHBOARD TABS
# ==========================================
tab_exec, tab_dept, tab_hr, tab_impact = st.tabs([
    "📈 Executive Overview", 
    "👥 Department Operations", 
    "⚠️ HR Monitor",
    "🌍 Field Operations & Impact"
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
    
    st.divider()
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1.container(border=True):
        st.write("### Roster Breakdown by Department")
        dept_counts = df_master["Department"].value_counts()
        # Adding a chart for department distribution with a color and container width
        st.bar_chart(dept_counts, color="#2C3E50", use_container_width=True)
        
    with col_chart2.container(border=True):
        st.write("### Standing Status Distribution")
        status_counts = df_master["SOP_Status"].value_counts()
        # Adding a bar chart for SOP_Status distribution with a specific color
        st.bar_chart(status_counts, color="#27AE60", use_container_width=True)

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
        df_filtered[["Volunteer ID", "Full_Name", "Contact (Email)", "Department", "Total_Events", "Present", "Attendance_Rate", "SOP_Status"]],
        use_container_width=True,
        hide_index=True,
        column_config={
        "Volunteer ID": st.column_config.TextColumn("ID", width="small"),
        "Full_Name": st.column_config.TextColumn("Volunteer Name", width="medium"),
        "Contact (Email)": st.column_config.TextColumn("Email Address", width="medium"),
        "Total_Events": st.column_config.NumberColumn("Total Events", format="%d 🗓️"),
        "Attendance_Rate": st.column_config.ProgressColumn(
            "Attendance Rate",
            help="Percentage of events attended",
            format="%.0f%%",
            min_value=0,
            max_value=100, # Assuming your math calculates out of 100
        ),
        "SOP_Status": st.column_config.TextColumn("Standing")
        }
    
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
                hide_index=True,
                column_config={
                    "Volunteer ID": st.column_config.TextColumn("ID"),
                    "Full_Name": st.column_config.TextColumn("Volunteer Name"),
                    "Total_Strikes": st.column_config.NumberColumn("⚠️ Strike Count", format="%d"),
                    "SOP_Status": st.column_config.TextColumn("Current Standing")
                }
            )

        else:
            st.success("No active strikes logged across the foundation!")
            
    with col_hr2:
        st.write("### 🎓 Certificate Eligible (Good Standing)")
        df_eligible = df_master[df_master["SOP_Status"] == "GOOD STANDING"]
        st.dataframe(
            df_eligible[["Volunteer ID", "Full_Name", "Department", "Attendance_Rate"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Volunteer ID": st.column_config.TextColumn("ID"),
                "Full_Name": st.column_config.TextColumn("Volunteer Name"),
                "Attendance_Rate": st.column_config.ProgressColumn(
                    "Attendance Rate",
                    format="%.0f%%",
                    min_value=0,
                    max_value=100
                )
            }
        )

    # ------------------------------------------
# TAB 4: FIELD OPERATIONS & IMPACT
# ------------------------------------------
with tab_impact:
    st.title("Field Operations Data Explorer")
    st.write("Raw data feed from the Drives Department:")
    
    # displaying the raw dataframe just to see the columns
    st.dataframe(df_drives, use_container_width=True)