import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time
import streamlit.components.v1 as components

# ==================== 1. CONFIG & ULTRA PREMIUM STYLE (EXACTLY AS YOURS) ====================
st.set_page_config(page_title="Event OS Pro | Willian's 26", page_icon="🎆", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
        background-image: linear-gradient(rgba(0, 0, 0, 0.9), rgba(0, 0, 0, 0.95)),
            url("https://images.unsplash.com/photo-1470225620780-dba8ba36b745?q=80&w=2070&auto=format&fit=crop");
        background-size: cover; background-attachment: fixed; color: #ffffff;
    }
    
    /* 🚀 ALL YOUR ORIGINAL CARD STYLES 🚀 */
    .card-student { background: rgba(16, 30, 45, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(0, 255, 255, 0.2); border-radius: 16px; padding: 20px; text-align: center; margin-bottom: 20px; }
    
    @keyframes pulse-purple { 0% { box-shadow: 0 0 0 0 rgba(213, 0, 249, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(213, 0, 249, 0); } 100% { box-shadow: 0 0 0 0 rgba(213, 0, 249, 0); } }
    .card-organizer { background: linear-gradient(135deg, rgba(40, 0, 80, 0.9), rgba(10, 0, 20, 0.9)); border: 2px solid #d500f9; border-radius: 16px; padding: 20px; text-align: center; animation: pulse-purple 2s infinite; }
    
    .card-staff { background: linear-gradient(145deg, #002b20, #001a13); border-top: 3px solid #00ff88; border-radius: 16px; padding: 20px; text-align: center; }
    
    .card-elite { background: linear-gradient(to bottom, #111, #222); border: 2px solid #ffd700; padding: 20px; text-align: center; position: relative; }
    .card-elite::after { content: "VIP ACCESS"; position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: #ffd700; color: black; font-weight: bold; font-size: 10px; padding: 2px 10px; border-radius: 10px; }

    .id-name { font-size: 28px; font-weight: bold; margin: 12px 0; color: white; }
    .info-row { display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.1); padding: 8px 0; font-size: 14px; color: #ccc; }
    .role-badge { background: rgba(255,255,255,0.1); padding: 4px 15px; border-radius: 20px; font-size: 11px; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

# ==================== 2. DATA ENGINE ====================
conn = st.connection("gsheets", type=GSheetsConnection)
BUS_CAPACITY = 45

def safe_update(ws, data):
    try:
        conn.update(worksheet=ws, data=data)
        return True
    except: return False

def load_data():
    try:
        df = conn.read(worksheet="Data", ttl=0)
        return df.fillna("N/A")
    except: return pd.DataFrame()

def load_stock():
    try:
        df_s = conn.read(worksheet="Stock", ttl=0)
        return dict(zip(df_s['Size'], df_s['Quantity'].astype(int)))
    except: return {"S":0, "M":0, "L":0, "XL":0, "XXL":0}

if 'df' not in st.session_state: st.session_state.df = load_data()
if 'stock' not in st.session_state: st.session_state.stock = load_stock()

# ==================== 3. LOGIN & MENU ====================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.title("🔐 Willian's 26 | Admin")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u == "admin" and p == "1234": st.session_state.logged_in = True; st.rerun()
    st.stop()

menu = st.sidebar.radio("Go To", ["🔍 Search & Entry", "➕ Add Staff", "🚌 Bus Manager", "📊 Dashboard", "📝 Admin Data"])

# --- SEARCH & ENTRY (WITH YOUR PREMIUM UI) ---
if menu == "🔍 Search & Entry":
    st.title("🔍 Search & Entry")
    q = st.text_input("🔎 Search...").strip()
    if q:
        res = st.session_state.df[st.session_state.df['Name'].str.contains(q, case=False) | st.session_state.df['Ticket_Number'].str.contains(q, case=False)]
        if not res.empty:
            idx = res.index[0]; row = st.session_state.df.loc[idx]
            role = row['Role']
            # Select Card Class
            c_class = "card-student"
            if role in ["Principal", "College Head"]: c_class = "card-elite"
            elif role == "Organizer": c_class = "card-organizer"
            elif role in ["Teacher", "Staff"]: c_class = "card-staff"
            
            st.markdown(f"""<div class="{c_class}">
                <span class="role-badge">{role}</span>
                <div class="id-name">{row['Name']}</div>
                <div class="info-row"><span>Ticket</span><span>{row['Ticket_Number']}</span></div>
                <div class="info-row"><span>Class</span><span>{row['Class']}</span></div>
                <div class="info-row"><span>Bus</span><span>{row['Bus_Number']}</span></div>
            </div>""", unsafe_allow_html=True)
            
            if st.button("Confirm Entry"):
                st.session_state.df.at[idx, 'Entry_Status'] = 'Done'
                if safe_update("Data", st.session_state.df): st.success("Check-in Done!"); st.rerun()

# --- BUS MANAGER (NEW: CLASS WISE & PDF) ---
elif menu == "🚌 Bus Manager":
    st.title("🚌 Fleet & Class Manager")
    buses = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    
    # NEW: Class-wise Selection System
    with st.expander("🎯 Class-wise Auto Assign", expanded=True):
        c1, c2, c3 = st.columns(3)
        sel_cls = c1.selectbox("Select Class", sorted(st.session_state.df['Class'].unique()))
        sel_bus = c2.selectbox("Select Bus", buses)
        if c3.button("Confirm Assign", use_container_width=True):
            mask = (st.session_state.df['Class'] == sel_cls) & (st.session_state.df['Bus_Number'] == 'Unassigned')
            indices = st.session_state.df[mask].index.tolist()
            cur_fill = len(st.session_state.df[st.session_state.df['Bus_Number'] == sel_bus])
            available = BUS_CAPACITY - cur_fill
            for i in indices[:available]:
                st.session_state.df.at[i, 'Bus_Number'] = sel_bus
            if safe_update("Data", st.session_state.df): st.success("Assigned!"); st.rerun()

    # NEW: PDF Manifest Output (Standard A4 Print Optimized)
    st.markdown("---")
    if st.button("📄 Generate PDF Manifest"):
        html = "<html><body style='font-family: sans-serif;'>"
        for b in buses:
            b_df = st.session_state.df[st.session_state.df['Bus_Number'] == b]
            if not b_df.empty:
                html += f"<h2>{b} List ({len(b_df)})</h2><table border='1' width='100%' style='border-collapse:collapse;'>"
                html += "<tr><th>SL</th><th>Name</th><th>Class</th><th>Sign</th></tr>"
                for i, (_, r) in enumerate(b_df.iterrows(), 1):
                    html += f"<tr><td>{i}</td><td>{r['Name']}</td><td>{r['Class']}</td><td>_______</td></tr>"
                html += "</table><div style='page-break-after:always;'></div>"
        html += "</body></html>"
        st.download_button("⬇️ Download PDF (HTML)", html, "Bus_Manifest.html", "text/html")

# --- DASHBOARD (NEW: STOCK REMAINING) ---
elif menu == "📊 Dashboard":
    st.title("📊 Event Insights")
    
    # NEW: Remaining Stock Calculation
    st.subheader("👕 T-Shirt Stock Remaining")
    cols = st.columns(5)
    for i, (size, total) in enumerate(st.session_state.stock.items()):
        taken = len(st.session_state.df[(st.session_state.df['T_Shirt_Size'] == size) & (st.session_state.df['T_Shirt_Collected'] == 'Yes')])
        remaining = total - taken
        cols[i].metric(f"Size {size}", f"{remaining} Left", f"Total: {total}")
    
    # Entry Status
    total_reg = len(st.session_state.df)
    total_entry = len(st.session_state.df[st.session_state.df['Entry_Status'] == 'Done'])
    st.metric("Total Attendance", f"{total_entry} / {total_reg}")

# --- ADMIN DATA ---
elif menu == "📝 Admin Data":
    st.title("📝 Full DB")
    st.dataframe(st.session_state.df, use_container_width=True)
    st.download_button("Download CSV", st.session_state.df.to_csv(), "data.csv")
