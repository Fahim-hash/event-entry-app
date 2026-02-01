import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# ==================== 0. PAGE CONFIG & CUSTOM CSS ====================
st.set_page_config(page_title="Event OS Pro", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px; padding: 15px; border: 1px solid #333;
    }
    .id-card {
        background: linear-gradient(135deg, #1f2937, #111827);
        padding: 20px; border-radius: 15px; color: #fff;
        text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        border: 1px solid #374151; margin-bottom: 20px;
    }
    .id-role { background: #facc15; color: #000; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 14px; }
    .id-name { font-size: 24px; font-weight: bold; margin: 10px 0; }
    .id-info { font-size: 15px; margin: 5px 0; color: #d1d5db; }
    .status-box {
        margin-top: 15px; padding: 10px; border-radius: 8px;
        background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== 1. LOGIN & SESSION ====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'logs' not in st.session_state:
    st.session_state.logs = []

def add_log(msg):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, f"[{t}] {msg}")

USERS = {"admin": "1234", "gate": "entry26"}

if not st.session_state.logged_in:
    st.title("🔐 Event OS Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USERS and USERS[u] == p:
            st.session_state.logged_in = True
            st.session_state.user_role = "admin" if u == "admin" else "volunteer"
            st.rerun()
    st.stop()

# ==================== 2. DATA ENGINE ====================
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Data", ttl=0)
        # কলাম লিস্ট চেক এবং মিসিং কলাম তৈরি
        required_cols = ['Name', 'Role', 'Spot Phone', 'Guardian Phone', 'Ticket_Number', 'Class', 'Roll', 'Entry_Status', 'Entry_Time', 'Bus_Number', 'T_Shirt_Size', 'T_Shirt_Collected', 'Food_Collected']
        for c in required_cols:
            if c not in df.columns: df[c] = ''
        
        # 'nan' এবং ডাটা টাইপ ফিক্স
        for col in df.columns:
            df[col] = df[col].astype(str).replace(['nan', 'None', ''], 'N/A')
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

if 'df' not in st.session_state:
    st.session_state.df = load_data()

# ==================== 3. DASHBOARD ====================
st.sidebar.title(f"👤 {st.session_state.user_role.upper()}")
menu = st.sidebar.radio("Menu", ["🏠 Dashboard", "🔍 Search & Entry", "⚙️ Admin Logs"])

if menu == "🏠 Dashboard":
    st.title("🚀 Command Center")
    df = st.session_state.df
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Pax", len(df))
    # Food_Collected এরর ফিক্সড
    food_count = len(df[df['Food_Collected'] == 'Yes']) if 'Food_Collected' in df.columns else 0
    c2.metric("Checked In", len(df[df['Entry_Status'] == 'Done']))
    c3.metric("Meals Served", food_count)
    
    st.markdown("---")
    st.subheader("📋 Recent Activity")
    st.dataframe(df[['Name', 'Role', 'Entry_Status']].tail(5), use_container_width=True)

# ==================== 4. SEARCH & ENTRY ====================
elif menu == "🔍 Search & Entry":
    st.title("🔍 Search Terminal")
    q = st.text_input("Search (Ticket/Name/Phone):").strip()
    
    if q:
        df = st.session_state.df
        mask = df['Name'].str.contains(q, case=False) | df['Ticket_Number'].str.contains(q, case=False) | df['Spot Phone'].str.contains(q, case=False)
        res = df[mask]
        
        if not res.empty:
            row_idx = res.index[0]
            row = df.loc[row_idx]
            
            # --- ডিজিটাল আইডি কার্ড ---
            st.markdown(f"""
            <div class="id-card">
                <div class="id-role">{row['Role']}</div>
                <div class="id-name">{row['Name']}</div>
                <div class="id-info">🎟 Ticket: {row['Ticket_Number']} | 🆔 Roll: {row['Roll']}</div>
                <div class="id-info">📞 Spot: {row['Spot Phone']} | 🚌 Bus: {row['Bus_Number']}</div>
                <div class="status-box">
                    <div style="color: {'#4ade80' if row['Entry_Status']=='Done' else '#f87171'}">
                        Entry: {'✅ DONE' if row['Entry_Status']=='Done' else '⏳ PENDING'}
                    </div>
                    <div style="color: {'#60a5fa' if row['T_Shirt_Collected']=='Yes' else '#9ca3af'}">
                        T-Shirt: {'✅ GIVEN' if row['T_Shirt_Collected']=='Yes' else '❌ NOT GIVEN'}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # --- কুইক অ্যাকশন ---
            with st.container(border=True):
                st.subheader("⚡ Quick Actions")
                c1, c2, c3 = st.columns(3)
                ent = c1.checkbox("Mark Entry", value=(row['Entry_Status']=='Done'))
                tsh = c2.checkbox("T-Shirt Given", value=(row['T_Shirt_Collected']=='Yes'))
                food = c3.checkbox("Food Served", value=(row['Food_Collected']=='Yes'))
                
                if st.button("Save Changes", type="primary", use_container_width=True):
                    st.session_state.df.at[row_idx, 'Entry_Status'] = 'Done' if ent else 'N/A'
                    st.session_state.df.at[row_idx, 'T_Shirt_Collected'] = 'Yes' if tsh else 'N/A'
                    st.session_state.df.at[row_idx, 'Food_Collected'] = 'Yes' if food else 'N/A'
                    
                    conn.update(worksheet="Data", data=st.session_state.df)
                    add_log(f"Updated {row['Name']}")
                    st.success("Updated Successfully!")
                    time.sleep(1)
                    st.rerun()
        else:
            st.warning("No user found!")

# ==================== 5. ADMIN LOGS ====================
elif menu == "⚙️ Admin Logs":
    st.title("📜 System Logs")
    if st.session_state.logs:
        for log in st.session_state.logs:
            st.text(log)
    else:
        st.info("No activity logs yet.")

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()
