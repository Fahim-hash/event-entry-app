import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time
import altair as alt

# ==============================================================================
# 0. SYSTEM CONFIGURATION & ADVANCED UI/UX
# ==============================================================================
st.set_page_config(page_title="Event OS Ultimate", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #e0e0e0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* Neon Glassmorphism Metric Cards */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(15px);
        border-radius: 18px; padding: 22px; 
        border: 1px solid rgba(0, 255, 255, 0.15);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        transition: all 0.3s ease;
    }
    div[data-testid="stMetric"]:hover { border-color: #00d2ff; transform: translateY(-3px); }
    
    /* Premium Digital ID Card */
    .id-card {
        background: linear-gradient(135deg, rgba(30, 30, 30, 0.9), rgba(15, 15, 15, 0.95));
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 25px; padding: 35px;
        color: #fff; text-align: center;
        box-shadow: 0 30px 60px rgba(0,0,0,0.8);
        margin-bottom: 25px;
    }
    .id-header { 
        background: linear-gradient(90deg, #00d2ff, #3a7bd5);
        padding: 15px; border-radius: 15px; font-weight: 900; text-transform: uppercase;
    }
    .id-name { font-size: 34px; font-weight: 900; margin: 20px 0; letter-spacing: -1px; }
    .id-info-row { 
        display: flex; justify-content: space-between; 
        border-bottom: 1px solid rgba(255,255,255,0.05); 
        padding: 10px 0; font-size: 16px; color: #ccc;
    }
    
    /* Visual Badges */
    .status-badge { font-weight: 800; padding: 8px 15px; border-radius: 10px; border: 1px solid; margin-top: 20px; text-align: center; }
    .notes-box { background: rgba(255, 75, 75, 0.1); border-left: 5px solid #ff4b4b; padding: 12px; border-radius: 8px; margin-top: 15px; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 1. SHARED DATA ENGINE
# ==============================================================================
if 'logs' not in st.session_state: st.session_state.logs = []
BUS_CAPACITY = 45 #

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Data", ttl=0)
        req_cols = ['Name', 'Role', 'Spot Phone', 'Guardian Phone', 'Ticket_Number', 
                    'Class', 'Roll', 'Entry_Status', 'Entry_Time', 'Bus_Number', 
                    'T_Shirt_Size', 'T_Shirt_Collected', 'Notes', 'Fault_Report', 'Image_URL']
        for c in req_cols:
            if c not in df.columns: df[c] = ''
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True).replace(['nan', 'None', ''], 'N/A')
        return df
    except: return pd.DataFrame()

def load_stock():
    try:
        df_s = conn.read(worksheet="Stock", ttl=0)
        stock = dict(zip(df_s['Size'], df_s['Quantity']))
        return {s: int(float(stock.get(s, 0))) for s in ["S", "M", "L", "XL", "XXL"]}
    except: return {"S":0, "M":0, "L":0, "XL":0, "XXL":0}

if 'df' not in st.session_state: st.session_state.df = load_data()
if 'stock' not in st.session_state: st.session_state.stock = load_stock()

# ==============================================================================
# 2. STUDENT PORTAL: LOGIN & FEATURES
# ==============================================================================
if 'portal_user' in st.session_state and st.session_state.portal_user:
    st.sidebar.title("🎓 Student Portal")
    user_tick = st.session_state.portal_user
    user_data = st.session_state.df[st.session_state.df['Ticket_Number'] == user_tick].iloc[0]

    p_menu = st.sidebar.radio("Navigation", ["🏠 Digital ID Card", "🚩 Report Faults", "📞 Contact Admin"])
    
    if p_menu == "🏠 Digital ID Card":
        st.title(f"Welcome, {user_data['Name']}")
        st.markdown(f"""
        <div class="id-card">
            <div class="id-header">Official Digital Pass</div>
            <div class="id-name">{user_data['Name']}</div>
            <div class="id-info-row"><span>Ticket No</span><span>{user_data['Ticket_Number']}</span></div>
            <div class="id-info-row"><span>Bus Number</span><span>{user_data['Bus_Number']}</span></div>
            <div class="id-info-row"><span>Check-In</span><span style="color:#00ff88;">{user_data['Entry_Status']}</span></div>
        </div>
        """, unsafe_allow_html=True)

    elif p_menu == "🚩 Report Faults":
        st.header("Help Us Fix Our Faults")
        with st.form("student_report"):
            report_msg = st.text_area("Detail your issue or complaint here:", placeholder="Type here...")
            file = st.file_uploader("Upload Evidence Picture", type=['jpg','png','jpeg'])
            if st.form_submit_button("Submit Complaint"):
                idx = st.session_state.df[st.session_state.df['Ticket_Number'] == user_tick].index[0]
                st.session_state.df.at[idx, 'Fault_Report'] = report_msg
                conn.update(worksheet="Data", data=st.session_state.df)
                st.success("Your report has been recorded and sent to the organisers.")

    elif p_menu == "📞 Contact Admin":
        st.header("Emergency Contact List")
        st.write("🚌 **Transport Lead:** +880 1XXXXXXXXX")
        st.write("🛠️ **Event Technical:** +880 1XXXXXXXXX")

    if st.sidebar.button("🚪 Logout Portal"):
        st.session_state.portal_user = None
        st.rerun()
    st.stop()

# ==============================================================================
# 3. STAFF TERMINAL: LOGIN & MANAGEMENT
# ==============================================================================
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center;'>⚡ Event Command Center</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔐 Staff Authentication", "🎓 Student Portal Login"])
    
    with t1:
        u = st.text_input("Username", key="u_staff")
        p = st.text_input("Password", type="password", key="p_staff")
        if st.button("Authorize Staff"):
            if u in ["admin", "gate"] and p in ["1234", "entry26"]:
                st.session_state.logged_in, st.session_state.user_role, st.session_state.user_name = True, u, u
                st.rerun()
            else: st.error("Access Denied")
    
    with t2:
        st.info("Log in with Ticket Number (ID) and Spot Phone (Password).")
        s_id = st.text_input("Ticket ID")
        s_ph = st.text_input("Spot Phone No", type="password")
        if st.button("Enter Portal"):
            match = st.session_state.df[(st.session_state.df['Ticket_Number'] == s_id) & (st.session_state.df['Spot Phone'] == s_ph)]
            if not match.empty:
                st.session_state.portal_user = s_id
                st.rerun()
            else: st.error("Record Not Found")
    st.stop()

# --- STAFF NAVIGATION ---
with st.sidebar:
    st.title("🛡️ Staff Terminal")
    menu = st.radio("Management Suite", ["🏠 Dashboard", "🔍 Search & Entry", "🚌 Transport", "📦 Inventory", "📊 Analytics", "⚙️ Logs"])
    if st.button("🔄 Cloud Refresh"):
        st.cache_data.clear()
        st.session_state.df, st.session_state.stock = load_data(), load_stock()
        st.rerun()
    if st.button("🚪 Staff Logout"):
        st.session_state.logged_in = False
        st.rerun()

# ==============================================================================
# 4. MODULES: DASHBOARD & SEARCH (WITH EDIT & UNASSIGN)
# ==============================================================================
if menu == "🏠 Dashboard":
    st.title("🚀 Event Overview")
    df = st.session_state.df
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total People", len(df))
    c2.metric("Checked In", len(df[df['Entry_Status'] == 'Done']))
    c3.metric("Kits Given", len(df[df['T_Shirt_Collected'] == 'Yes']))
    c4.metric("Student Reports", len(df[df['Fault_Report'] != 'N/A']))
    
    st.subheader("Live Entry Data")
    st.dataframe(df[df['Entry_Status']=='Done'].sort_values('Entry_Time', ascending=False).head(10), use_container_width=True)

elif menu == "🔍 Search & Entry":
    st.title("🔍 Access & Edit Interface")
    q = st.text_input("Scan Ticket / Name / Phone:").strip()
    
    if q:
        df = st.session_state.df
        mask = df['Name'].str.contains(q, case=False) | df['Ticket_Number'].str.contains(q, case=False) | df['Spot Phone'].str.contains(q, case=False)
        res = df[mask]
        
        if not res.empty:
            idx = res.index[0]
            row = df.loc[idx]
            
            # --- Visual Indicators & ID Card ---
            is_ent = row['Entry_Status'] == 'Done'
            color = "#00ff88" if is_ent else "#ff4b4b"
            
            col1, col2 = st.columns([1, 1.5])
            with col1:
                st.markdown(f"""
                <div class="id-card" style="border: 2px solid {color};">
                    <div class="id-header" style="background:{color};">{'VERIFIED' if is_ent else 'PENDING'}</div>
                    <div class="id-name">{row['Name']}</div>
                    <div class="id-info-row"><span>Ticket</span><span>{row['Ticket_Number']}</span></div>
                    <div class="id-info-row"><span>Bus</span><span>{row['Bus_Number']}</span></div>
                    <div class="notes-box">Staff Notes: {row['Notes']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if row['Fault_Report'] != 'N/A':
                    st.error(f"⚠️ Student Complaint: {row['Fault_Report']}")

            with col2:
                with st.form("master_edit"):
                    st.subheader("📝 Universal Profile Editor")
                    ca, cb = st.columns(2)
                    e_name = ca.text_input("Full Name", row['Name'])
                    e_ph = cb.text_input("Spot Phone (Required)", row['Spot Phone'])
                    
                    cc, cd = st.columns(2)
                    e_tk = cc.text_input("Ticket Number (Required)", row['Ticket_Number'])
                    e_rl = cd.text_input("Roll Number", row['Roll'])
                    
                    st.markdown("---")
                    ce, cf = st.columns(2)
                    mark_ent = ce.toggle("Check-In Accomplished", value=is_ent)
                    mark_kit = cf.toggle("Merchandise Distributed", value=(row['T_Shirt_Collected']=='Yes'))
                    
                    e_sz = st.selectbox("Update Size", ["S", "M", "L", "XL", "XXL"], index=2)
                    e_notes = st.text_area("Update Notes", value=row['Notes'])
                    
                    if st.form_submit_button("💾 Synchronize with Cloud"):
                        if mark_ent and (e_ph in ['N/A', ''] or e_tk in ['N/A', '']):
                            st.error("❌ Phone and Ticket are MANDATORY for entry!")
                        else:
                            st.session_state.df.at[idx, 'Name'] = e_name
                            st.session_state.df.at[idx, 'Spot Phone'] = e_ph
                            st.session_state.df.at[idx, 'Ticket_Number'] = e_tk
                            st.session_state.df.at[idx, 'Roll'] = e_rl
                            st.session_state.df.at[idx, 'Entry_Status'] = 'Done' if mark_ent else 'N/A'
                            st.session_state.df.at[idx, 'T_Shirt_Collected'] = 'Yes' if mark_kit else 'No'
                            st.session_state.df.at[idx, 'T_Shirt_Size'] = e_sz
                            st.session_state.df.at[idx, 'Notes'] = e_notes
                            if mark_ent and row['Entry_Time'] == 'N/A': st.session_state.df.at[idx, 'Entry_Time'] = datetime.now().strftime("%H:%M:%S")
                            conn.update(worksheet="Data", data=st.session_state.df)
                            st.success("Synchronized!"); time.sleep(0.5); st.rerun()

                if row['Bus_Number'] != 'Unassigned':
                    if st.button("❌ UNASSIGN BUS FROM DASHBOARD", type="secondary", use_container_width=True):
                        st.session_state.df.at[idx, 'Bus_Number'] = 'Unassigned'
                        conn.update(worksheet="Data", data=st.session_state.df)
                        st.rerun()
        else: st.warning("No Results Found")

# --- MODULE: TRANSPORT (SMART OVERFLOW) ---
elif menu == "🚌 Transport":
    st.title("🚌 Logistics & Fleet Manager")
    buses = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    cols = st.columns(4)
    for i, b in enumerate(buses):
        occ = len(st.session_state.df[st.session_state.df['Bus_Number'] == b])
        cols[i].metric(b, f"{occ}/{BUS_CAPACITY}", f"{BUS_CAPACITY-occ} Free")
        cols[i].progress(min(occ/BUS_CAPACITY, 1.0))
    
    with st.expander("🚀 Smart Group Assignment (Auto-Overflow)"):
        ca, cb, cc = st.columns(3)
        mode = ca.selectbox("Assign By", ["Class", "Role"])
        val = cb.selectbox("Target Group", sorted(st.session_state.df[mode].unique()))
        start = cc.selectbox("Start Bus", buses)
        
        if st.button("Initiate Smart Assign"):
            indices = st.session_state.df[st.session_state.df[mode] == val].index.tolist()
            b_idx = buses.index(start)
            for p_idx in indices:
                while b_idx < 4:
                    if len(st.session_state.df[st.session_state.df['Bus_Number'] == buses[b_idx]]) < BUS_CAPACITY:
                        st.session_state.df.at[p_idx, 'Bus_Number'] = buses[b_idx]
                        break
                    else: b_idx += 1 # Overflow Logic
            conn.update(worksheet="Data", data=st.session_state.df)
            st.success("Group Logistics Updated!"); st.rerun()
