import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- CONFIG ---
def init_page(title):
    st.set_page_config(page_title=title, page_icon="⚡", layout="wide")
    st.markdown("""
        <style>
        .stApp { background-color: #050505; color: #e0e0e0; }
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(0, 255, 255, 0.1);
            border-radius: 15px; padding: 15px;
        }
        .id-card {
            background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
            border: 1px solid #444; border-radius: 20px; padding: 20px;
            text-align: center; margin-bottom: 20px;
        }
        .notes-box {
            background: rgba(255, 255, 255, 0.1); border-left: 5px solid #ff4b4b;
            padding: 10px; border-radius: 5px; margin-top: 10px; font-style: italic;
        }
        </style>
    """, unsafe_allow_html=True)

# --- SESSION & LOGS FIX ---
def init_session():
    if 'logs' not in st.session_state: st.session_state.logs = []
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

def add_log(msg):
    t = datetime.now().strftime("%H:%M:%S")
    user = st.session_state.get('user_name', 'System')
    st.session_state.logs.insert(0, f"[{t}] {user}: {msg}")

# --- DATA LOADING FIX ---
def get_conn(): return st.connection("gsheets", type=GSheetsConnection)

def load_data():
    conn = get_conn()
    try:
        df = conn.read(worksheet="Data", ttl=0)
        # সব কলাম নিশ্চিত করা (যাতে KeyError না আসে)
        req = ['Name', 'Role', 'Spot Phone', 'Guardian Phone', 'Ticket_Number', 'Class', 'Roll', 
               'Entry_Status', 'Entry_Time', 'Bus_Number', 'T_Shirt_Size', 'T_Shirt_Collected', 
               'Notes', 'Fault_Report', 'Food_Collected']
        for c in req:
            if c not in df.columns: df[c] = ''
            
        # .0 সমস্যা সমাধান
        for c in df.columns:
            df[c] = df[c].astype(str).str.replace(r'\.0$', '', regex=True).replace(['nan', 'None', ''], 'N/A')
        return df
    except: return pd.DataFrame()

def load_stock():
    try:
        df = get_conn().read(worksheet="Stock", ttl=0)
        stock = dict(zip(df['Size'], df['Quantity']))
        return {s: int(float(stock.get(s, 0))) for s in ["S", "M", "L", "XL", "XXL"]}
    except: return {"S":0, "M":0, "L":0, "XL":0, "XXL":0}