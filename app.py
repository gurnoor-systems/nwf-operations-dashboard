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

ATTENDANCE_URL = "https://docs.google.com/spreadsheets/d/1FN3dwVcuEyTwjoQTsyY-ABKmXEQKk5CBsLs6dLXaAVQ/edit"

DIRECTORY_URL = "https://docs.google.com/spreadsheets/d/19X1b-B2nL5u02vhqxNAEcvdY9J_URo2lG1oTii58Mc0/edit"

DRIVES_URL = "https://docs.google.com/spreadsheets/d/1wL81j3QWoHUO4_6AHA9BEnEhwzLe1KtHDIOceI446Og/edit"

EDU_URL = "https://docs.google.com/spreadsheets/d/1YFmTWXJGH52kyLQ6lICeFbV0aOh7RZ9xZJK4nWfQUoc/edit"

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

@st.cache_data(ttl=300)
def load_education_master():
    return conn.read(spreadsheet=EDU_URL, worksheet="Student Master File")

@st.cache_data(ttl=300)
def load_education_survey():
    return conn.read(spreadsheet=EDU_URL, worksheet="Survey Department Log")

@st.cache_data(ttl=300)
def load_education_log():
    return conn.read(spreadsheet=EDU_URL, worksheet="Educating Log")

try:
# 1. Load the Strike Data
    df_master = load_strike_summary()
    df_master = df_master[~df_master["Department"].str.contains("Void", case=False, na=False)]
    
# 2. Load the Directory Data
    df_dir = load_directory()
    
    df_dir_clean = df_dir[["Volunteer ID", "Contact (Email)"]] 
    
    # 2. The Merge: Joining the clean directory to the strike summary
    df_master = pd.merge(df_master, df_dir_clean, on="Volunteer ID", how="left")
    
    # 3. Clean Data Types
    df_master["Total_Strikes"] = pd.to_numeric(df_master["Total_Strikes"], errors="coerce").fillna(0)
    df_master["Total_Events"] = pd.to_numeric(df_master["Total_Events"], errors="coerce").fillna(0)
    df_master["Present"] = pd.to_numeric(df_master["Present"], errors="coerce").fillna(0)

# 3. Load Drives Impact Data
    df_drives = load_drives_data()

# 4. Drop empty rows that Google Sheets accidentally sends

    # Strip invisible spaces from all column headers instantly
    df_drives.columns = df_drives.columns.str.strip()
    df_drives = df_drives.dropna(subset=["Date"])
    # Convert Beneficiaries to a number so we can add them up
    df_drives["No. of Beneficiaries"] = pd.to_numeric(df_drives["No. of Beneficiaries"], errors="coerce").fillna(0)

# 5. Load Education Data & Apply Privacy Filter
    df_edu = load_education_master()
    
    # Strip invisible spaces from headers (Defensive Engineering)
    df_edu.columns = df_edu.columns.str.strip()
    
    # Define the strict list of PII columns that must not be sent to the UI
    pii_columns = ["Parent/Guardian Contact", "Parents Name", "Address", "Background / Notes"]
    
    # Droping the PII columns
    df_edu_safe = df_edu.drop(columns=pii_columns, errors='ignore')
    
    # Drop completely empty rows where a Student ID doesn't exist
    df_edu_safe = df_edu_safe.dropna(subset=["Student ID"])

# 6. Load Survey Data
    df_edu_survey = load_education_survey()
    df_edu_survey.columns = df_edu_survey.columns.str.strip() # Defensive engineering
    df_edu_survey = df_edu_survey.dropna(subset=["Date"])
    df_edu_survey["Families Approached"] = pd.to_numeric(df_edu_survey["Families Approached"], errors="coerce").fillna(0)
    
# 7. Load Educating Log Data
    df_edu_log = load_education_log()
    df_edu_log.columns = df_edu_log.columns.str.strip()
    df_edu_log = df_edu_log.dropna(subset=["Date"])
    
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
    st.title("Field Operations & Community Impact")
    st.write("Real-time metrics from the Drives Department.")
    
    # Calculate KPIs
    completed_drives = len(df_drives[df_drives["Status"] == "Completed"])
    total_beneficiaries = int(df_drives["No. of Beneficiaries"].sum())
    unique_locations = df_drives["Date & Location"].nunique()
    
    # Render KPI Cards
    col1, col2, col3 = st.columns(3)
    with col1.container(border=True):
        st.metric("Total Drives Executed", f"{completed_drives} 🚐")
    with col2.container(border=True):
        st.metric("Beneficiaries Impacted", f"{total_beneficiaries} 🤝")
    with col3.container(border=True):
        st.metric("Partner Locations", f"{unique_locations} 🏥")
        
    st.divider()
    
    # Render the cleaned table
    st.write("### 📋 Recent Drive Logs")
    st.dataframe(
        df_drives[["Drive ID", "Date", "Date & Location", "Type of Care Home", "Status", "No. of Beneficiaries"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn("Status"),
            "No. of Beneficiaries": st.column_config.NumberColumn("Beneficiaries", format="%d")
        }
    )

# ==========================================
# EDUCATION DEPARTMENT METRICS
# ==========================================

    st.write("---")
    st.write("### 📚 Education Department Operations")
    
    # Calculate Advanced Education KPIs
    total_students = len(df_edu_safe)
    active_educators = df_edu_log["Educator ID"].nunique()
    families_approached = int(df_edu_survey["Families Approached"].sum())
    total_sessions = len(df_edu_log)
    
    # Render 4 Dynamic KPI Cards
    col_edu1, col_edu2, col_edu3, col_edu4 = st.columns(4)
    with col_edu1.container(border=True):
        st.metric("Enrolled Students", f"{total_students} 🧑‍🎓")
    with col_edu2.container(border=True):
        st.metric("Active Educators", f"{active_educators} 🧑‍🏫")
    with col_edu3.container(border=True):
        st.metric("Families Approached", f"{families_approached} 🏘️")
    with col_edu4.container(border=True):
        st.metric("Teaching Sessions", f"{total_sessions} 📝")
        
    st.write("#### 🧑‍🎓 Anonymized Student Roster")
    st.caption("Privacy Notice: PII (Phone numbers, Parent Names, Addresses) are strictly masked at the database level and omitted from this portal.")
    
    st.dataframe(
        df_edu_safe,
        use_container_width=True,
        hide_index=True
    )