import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time
import random
import streamlit.components.v1 as components

# ==================== 1. CONFIG & STYLE ====================
st.set_page_config(page_title="Event OS Pro | Willian's 26", page_icon="🎆", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    
    /* Bus Manager Visuals */
    .bus-container {
        background: rgba(20, 20, 20, 0.8);
        border: 1px solid #333;
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        margin-bottom: 20px;
    }
    .seat-grid { font-family: monospace; font-size: 14px; line-height: 1.2; letter-spacing: 3px; color: #00ff88; }
    
    /* Cards for Search */
    .card-student { background: rgba(16, 30, 45, 0.7); border: 1px solid #00ffff; border-radius: 16px; padding: 20px; text-align: center; }
    .id-name { font-size: 26px; font-weight: bold; margin: 10px 0; }
    .info-row { display: flex; justify-content: space-between; border-bottom: 1px solid #222; padding: 5px 0; }
    </style>
    """, unsafe_allow_html=True)

# ==================== 2. DATA ENGINE ====================
conn = st.connection("gsheets", type=GSheetsConnection)
BUS_CAPACITY = 45

def safe_update(ws, data):
    try:
        conn.update(worksheet=ws, data=data)
        return True
    except Exception as e:
        st.error(f"⚠️ Cloud Sync Error: {e}")
        return False

def load_data():
    try:
        df = conn.read(worksheet="Data", ttl=0)
        req_cols = ['Name', 'Role', 'Spot Phone', 'Guardian Phone', 'Ticket_Number', 'Class', 'Roll', 'Entry_Status', 'Entry_Time', 'Bus_Number', 'T_Shirt_Size', 'T_Shirt_Collected', 'Notes']
        for c in req_cols:
            if c not in df.columns: df[c] = 'N/A'
        return df.fillna("N/A")
    except: return pd.DataFrame()

if 'df' not in st.session_state: st.session_state.df = load_data()

# ==================== 3. LOGIN ====================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.title("🔐 Willian's 26 | Admin")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u == "admin" and p == "1234":
            st.session_state.logged_in = True; st.rerun()
    st.stop()

# ==================== 4. MENU ====================
st.sidebar.title("⚡ Menu")
menu = st.sidebar.radio("Go To", ["🔍 Search & Entry", "➕ Add Staff/Teacher", "🚌 Bus Manager", "📝 Admin Data"])

if st.sidebar.button("🔄 Refresh Sheets"):
    st.session_state.df = load_data(); st.rerun()

# --- SEARCH & ENTRY ---
if menu == "🔍 Search & Entry":
    st.title("🔍 Search & Entry")
    q = st.text_input("Search (Ticket/Name/Phone):")
    if q:
        res = st.session_state.df[st.session_state.df['Name'].str.contains(q, case=False) | st.session_state.df['Ticket_Number'].str.contains(q, case=False)]
        if not res.empty:
            idx = res.index[0]; row = st.session_state.df.loc[idx]
            st.markdown(f"""<div class="card-student"><div class="id-name">{row['Name']}</div><div class="info-row"><span>Class:</span><span>{row['Class']}</span></div><div class="info-row"><span>Bus:</span><span>{row['Bus_Number']}</span></div></div>""", unsafe_allow_html=True)
            if st.button("✅ Mark Entry"):
                st.session_state.df.at[idx, 'Entry_Status'] = 'Done'
                if safe_update("Data", st.session_state.df): st.success("Done!"); st.rerun()
        else: st.warning("Not Found")

# --- ADD STAFF ---
elif menu == "➕ Add Staff/Teacher":
    st.title("➕ Add Entry")
    with st.form("add"):
        name = st.text_input("Name"); ph = st.text_input("Phone")
        role = st.selectbox("Role", ["Teacher", "Volunteer", "Staff"])
        if st.form_submit_button("Add"):
            new = {'Name':name, 'Role':role, 'Spot Phone':ph, 'Bus_Number':'Unassigned', 'Entry_Status':'N/A'}
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new])], ignore_index=True)
            if safe_update("Data", st.session_state.df): st.success("Added!"); st.rerun()

# --- BUS MANAGER (NEW VISUALS + CLASS WISE RANDOM) ---
elif menu == "🚌 Bus Manager":
    st.title("🚌 Fleet & Random Seating")
    
    buses = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    
    # --- Visualisation ---
    cols = st.columns(4)
    for i, b in enumerate(buses):
        df_b = st.session_state.df[st.session_state.df['Bus_Number'] == b]
        cnt = len(df_b)
        with cols[i]:
            st.metric(b, f"{cnt}/{BUS_CAPACITY}")
            grid = ""
            for s in range(BUS_CAPACITY):
                grid += "🔵" if s < cnt else "⚪"
                if (s+1) % 4 == 0: grid += "<br>"
            st.markdown(f"<div class='seat-grid'>{grid}</div>", unsafe_allow_html=True)

    st.markdown("---")
    
    # --- Class-wise Random Assign ---
    st.subheader("🎲 Class-wise Random Assign")
    classes = sorted(st.session_state.df['Class'].unique())
    sel_class = st.selectbox("Select Class to Assign", classes)
    
    if st.button("🚀 Assign Class Randomly"):
        # যারা ওই ক্লাসের এবং এখনো বাসে নাই
        unassigned = st.session_state.df[(st.session_state.df['Class'] == sel_class) & (st.session_state.df['Bus_Number'] == 'Unassigned')].index.tolist()
        
        if not unassigned:
            st.warning(f"No unassigned students in {sel_class}")
        else:
            random.shuffle(unassigned) # লটারি/র‍্যান্ডম করা হলো
            count = 0
            for b in buses:
                curr_count = len(st.session_state.df[st.session_state.df['Bus_Number'] == b])
                free = BUS_CAPACITY - curr_count
                while free > 0 and unassigned:
                    idx = unassigned.pop()
                    st.session_state.df.at[idx, 'Bus_Number'] = b
                    free -= 1; count += 1
            
            if safe_update("Data", st.session_state.df):
                st.success(f"Successfully assigned {count} students from {sel_class} randomly!"); time.sleep(1); st.rerun()

# --- ADMIN DATA ---
elif menu == "📝 Admin Data":
    st.title("📝 Database View")
    st.dataframe(st.session_state.df)
