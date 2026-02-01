import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# ==================== 0. PAGE CONFIG ====================
st.set_page_config(page_title="Event OS Ultimate", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #e0e0e0; }
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 15px; padding: 20px; border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .id-card {
        background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
        border: 2px solid #333; border-radius: 20px; padding: 20px;
        color: #fff; text-align: center; box-shadow: 0 20px 50px rgba(0,0,0,0.5);
    }
    .id-header { background: linear-gradient(90deg, #00c6ff, #0072ff); padding: 10px; border-radius: 10px; font-weight: bold; }
    .id-name { font-size: 28px; font-weight: 800; margin: 15px 0; }
    .id-info-row { display: flex; justify-content: space-between; border-bottom: 1px solid #333; padding: 5px 0; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# ==================== 1. LOGIN SYSTEM ====================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

USERS = {"admin": "1234", "gate": "entry26"}

if not st.session_state.logged_in:
    st.title("🔐 Event OS Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Access"):
        if u in USERS and USERS[u] == p:
            st.session_state.logged_in, st.session_state.user_role = True, ("admin" if u=="admin" else "gate")
            st.rerun()
    st.stop()

# ==================== 2. DATA ENGINE ====================
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Data", ttl=0)
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True).replace(['nan', 'None', ''], 'N/A')
        return df
    except: return pd.DataFrame()

if 'df' not in st.session_state: st.session_state.df = load_data()

# ==================== 3. NAVIGATION ====================
menu = st.sidebar.radio("Navigate", ["🏠 Dashboard", "🔍 Search & Entry", "🚌 Bus Fleet"])

# --- 🔍 SEARCH & ENTRY (EDIT OPTION HERE) ---
if menu == "🔍 Search & Entry":
    st.title("🔍 Search & Edit Profile")
    q = st.text_input("Search by Name/Ticket/Phone:").strip()
    
    if q:
        df = st.session_state.df
        res = df[df['Name'].str.contains(q, case=False) | df['Ticket_Number'].str.contains(q, case=False) | df['Spot Phone'].str.contains(q, case=False)]
        
        if not res.empty:
            idx = res.index[0]
            row = df.loc[idx]
            
            col1, col2 = st.columns([1, 1.5])
            with col1:
                st.markdown(f"""
                <div class="id-card">
                    <div class="id-header">PASSENGER INFO</div>
                    <div class="id-name">{row['Name']}</div>
                    <div class="id-info-row"><span>Ticket</span><span>{row['Ticket_Number']}</span></div>
                    <div class="id-info-row"><span>Roll</span><span>{row['Roll']}</span></div>
                    <div class="id-info-row"><span>Phone</span><span>{row['Spot Phone']}</span></div>
                    <div class="id-info-row"><span>Bus</span><span>{row['Bus_Number']}</span></div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                # 🔥 EDIT SECTION START 🔥
                st.subheader("📝 Edit Information")
                with st.form("edit_info_form"):
                    new_name = st.text_input("Name", value=row['Name'])
                    new_phone = st.text_input("Spot Phone", value=row['Spot Phone'])
                    new_ticket = st.text_input("Ticket Number", value=row['Ticket_Number'])
                    new_roll = st.text_input("Roll", value=row['Roll'])
                    
                    # Admin specific edits
                    if st.session_state.user_role == 'admin':
                        bus_list = ["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"]
                        new_bus = st.selectbox("Assign Bus", bus_list, index=bus_list.index(row['Bus_Number']) if row['Bus_Number'] in bus_list else 0)
                        new_role = st.selectbox("Role", ["Student", "Volunteer", "Teacher", "Organizer"], index=0)
                    
                    if st.form_submit_button("💾 Save & Sync Data"):
                        st.session_state.df.at[idx, 'Name'] = new_name
                        st.session_state.df.at[idx, 'Spot Phone'] = new_phone
                        st.session_state.df.at[idx, 'Ticket_Number'] = new_ticket
                        st.session_state.df.at[idx, 'Roll'] = new_roll
                        
                        if st.session_state.user_role == 'admin':
                            st.session_state.df.at[idx, 'Bus_Number'] = new_bus
                            st.session_state.df.at[idx, 'Role'] = new_role
                        
                        conn.update(worksheet="Data", data=st.session_state.df)
                        st.success("Information Updated Successfully!")
                        time.sleep(1)
                        st.rerun()
        else: st.warning("No matches found!")

# (অন্যান্য মডিউল যেমন Dashboard ও Bus Fleet আগের মতোই থাকবে)
