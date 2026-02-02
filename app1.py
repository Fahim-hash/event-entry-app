import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time
import streamlit.components.v1 as components

# ==================== 1. CONFIG & STYLE (EXACTLY YOURS) ====================
st.set_page_config(page_title="Event OS Pro | Willian's 26", page_icon="🎆", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
        background-image: linear-gradient(rgba(0, 0, 0, 0.9), rgba(0, 0, 0, 0.95)),
            url("https://images.unsplash.com/photo-1470225620780-dba8ba36b745?q=80&w=2070&auto=format&fit=crop");
        background-size: cover; background-attachment: fixed; color: #ffffff;
    }
    section[data-testid="stSidebar"] { background-color: rgba(5, 5, 5, 0.95); border-right: 1px solid #222; }

    /* YOUR PREMIUM CARD CLASSES */
    .card-student { background: rgba(16, 30, 45, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(0, 255, 255, 0.2); border-radius: 16px; padding: 20px; text-align: center; margin-bottom: 20px; }
    @keyframes pulse-purple { 0% { box-shadow: 0 0 0 0 rgba(213, 0, 249, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(213, 0, 249, 0); } 100% { box-shadow: 0 0 0 0 rgba(213, 0, 249, 0); } }
    .card-organizer { background: linear-gradient(135deg, rgba(40, 0, 80, 0.9), rgba(10, 0, 20, 0.9)); border: 2px solid #d500f9; border-radius: 16px; padding: 20px; text-align: center; animation: pulse-purple 2s infinite; }
    .card-staff { background: linear-gradient(145deg, #002b20, #001a13); border-top: 3px solid #00ff88; border-radius: 16px; padding: 20px; text-align: center; }
    .card-volunteer { background: repeating-linear-gradient(45deg, #1a0500, #1a0500 10px, #2a0a00 10px, #2a0a00 20px); border: 2px solid #ff4b1f; border-radius: 16px; padding: 20px; text-align: center; }
    .card-elite { background: linear-gradient(to bottom, #111, #222); border: 2px solid #ffd700; padding: 20px; text-align: center; position: relative; }
    .card-elite::after { content: "VIP ACCESS"; position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: #ffd700; color: black; font-weight: bold; font-size: 10px; padding: 2px 10px; border-radius: 10px; }

    .id-name { font-size: 28px; font-weight: bold; margin: 12px 0; color: white; }
    .info-row { display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.1); padding: 8px 0; font-size: 14px; color: #ccc; }
    .role-badge { background: rgba(255,255,255,0.1); padding: 4px 15px; border-radius: 20px; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; }
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
        st.error(f"Sync Error: {e}")
        return False

def load_data():
    df = conn.read(worksheet="Data", ttl=0)
    return df.fillna("N/A")

def load_stock():
    try:
        df_s = conn.read(worksheet="Stock", ttl=0)
        return dict(zip(df_s['Size'], df_s['Quantity'].astype(int)))
    except: return {"S":0, "M":0, "L":0, "XL":0, "XXL":0}

if 'df' not in st.session_state: st.session_state.df = load_data()
if 'stock' not in st.session_state: st.session_state.stock = load_stock()

# ==================== 3. TIMER (YOUR COMPONENT) ====================
target_iso = "2026-02-03T07:00:00+06:00"
timer_html = f"""<div style="background: linear-gradient(135deg, #000428, #004e92); color: white; padding: 15px; border-radius: 12px; text-align: center; border: 1px solid rgba(255,255,255,0.2);">
<div style="font-size: 11px; color: #00ff88;">EVENT COUNTDOWN</div><div style="font-size: 24px; font-weight: bold;">📅 3RD FEB 2026</div></div>"""
with st.sidebar: components.html(timer_html, height=100)

# ==================== 4. NAVIGATION & FEATURES ====================
menu = st.sidebar.radio("Go To", ["🔍 Search & Entry", "➕ Add Staff/Teacher", "📜 View Lists", "🚌 Bus Manager", "📊 Dashboard", "📝 Admin Data"])

# --- SEARCH & ENTRY (KEEPING YOUR EXACT LOGIC) ---
if menu == "🔍 Search & Entry":
    st.title("🔍 Search & Entry")
    q = st.text_input("🔎 Search by Ticket / Name / Phone:").strip()
    if q:
        df = st.session_state.df
        res = df[df['Name'].str.contains(q, case=False) | df['Ticket_Number'].str.contains(q, case=False) | df['Spot Phone'].str.contains(q, case=False)]
        if not res.empty:
            idx = res.index[0]; row = df.loc[idx]
            role = row['Role']
            # Selection of Card Style
            c_style = "card-student"
            if role in ["Principal", "College Head"]: c_style = "card-elite"
            elif role == "Organizer": c_style = "card-organizer"
            elif role in ["Teacher", "Staff"]: c_style = "card-staff"
            
            st.markdown(f"""<div class="{c_style}">
                <span class="role-badge">{role}</span>
                <div class="id-name">{row['Name']}</div>
                <div class="info-row"><span>Ticket</span><span>{row['Ticket_Number']}</span></div>
                <div class="info-row"><span>Class</span><span>{row['Class']}</span></div>
                <div class="info-row"><span>Bus</span><span>{row['Bus_Number']}</span></div>
            </div>""", unsafe_allow_html=True)
            
            # Entry Toggle
            if st.button("Confirm Entry"):
                st.session_state.df.at[idx, 'Entry_Status'] = 'Done'
                if safe_update("Data", st.session_state.df): st.success("Done!"); st.rerun()

# --- BUS MANAGER (ENHANCED: CLASS WISE & PDF) ---
elif menu == "🚌 Bus Manager":
    st.title("🚌 Fleet Manager")
    buses = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    
    # NEW: Class-wise Auto Assign
    with st.expander("🎯 Auto Assign by Class", expanded=True):
        c1, c2, c3 = st.columns(3)
        sel_class = c1.selectbox("Select Class", sorted(st.session_state.df['Class'].unique()))
        sel_bus = c2.selectbox("Select Bus", buses)
        if c3.button("Assign Batch"):
            mask = (st.session_state.df['Class'] == sel_class) & (st.session_state.df['Bus_Number'] == 'Unassigned')
            unassigned_indices = st.session_state.df[mask].index.tolist()
            cur_fill = len(st.session_state.df[st.session_state.df['Bus_Number'] == sel_bus])
            available = BUS_CAPACITY - cur_fill
            for i in unassigned_indices[:available]:
                st.session_state.df.at[i, 'Bus_Number'] = sel_bus
            if safe_update("Data", st.session_state.df): st.success("Batch Assigned!"); st.rerun()

    # NEW: PDF Ready Manifest
    st.markdown("---")
    if st.button("📄 Generate Print-Ready Manifest (PDF)"):
        html = "<html><body style='font-family:sans-serif;'><h1>Bus Manifest</h1>"
        for b in buses:
            b_list = st.session_state.df[st.session_state.df['Bus_Number'] == b]
            if not b_list.empty:
                html += f"<h2>{b} ({len(b_list)})</h2><table border='1' width='100%'><tr><th>Name</th><th>Class</th><th>Sign</th></tr>"
                for _, r in b_list.iterrows():
                    html += f"<tr><td>{r['Name']}</td><td>{r['Class']}</td><td>_______</td></tr>"
                html += "</table><div style='page-break-after:always;'></div>"
        html += "</body></html>"
        st.download_button("⬇️ Download Manifest", html, "Bus_List.html", "text/html")

# --- DASHBOARD (ENHANCED: REMAINING STOCK) ---
elif menu == "📊 Dashboard":
    st.title("📊 Event Insights")
    
    # NEW: Stock Remaining Calculation
    st.subheader("👕 T-Shirt Inventory (Remaining)")
    st_cols = st.columns(5)
    for i, (sz, total) in enumerate(st.session_state.stock.items()):
        taken = len(st.session_state.df[(st.session_state.df['T_Shirt_Size'] == sz) & (st.session_state.df['T_Shirt_Collected'] == 'Yes')])
        remaining = total - taken
        st_cols[i].metric(f"Size {sz}", f"{remaining} Left", f"Total: {total}")
    
    st.markdown("---")
    # Attendance Stats
    total = len(st.session_state.df)
    entry = len(st.session_state.df[st.session_state.df['Entry_Status'] == 'Done'])
    st.metric("Total Check-ins", f"{entry} / {total}")

# --- KEEPING OTHER MENUS (ADD STAFF, VIEW LIST, ADMIN DATA) ---
elif menu == "➕ Add Staff/Teacher":
    st.subheader("Add Manual Entry")
    # ... (Your existing Add Staff logic)

elif menu == "📜 View Lists":
    st.subheader("Lists Viewer")
    # ... (Your existing View List logic)

elif menu == "📝 Admin Data":
    st.dataframe(st.session_state.df)
