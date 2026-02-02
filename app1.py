import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time
import pytz
import streamlit.components.v1 as components

# ==================== 1. CONFIG & STYLE (ULTRA PREMIUM) ====================
st.set_page_config(page_title="Event OS Pro | Willian's 26", page_icon="🎆", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
        background-image: 
            linear-gradient(rgba(0, 0, 0, 0.9), rgba(0, 0, 0, 0.95)),
            url("https://images.unsplash.com/photo-1470225620780-dba8ba36b745?q=80&w=2070&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
        color: #ffffff;
    }
    section[data-testid="stSidebar"] { background-color: rgba(5, 5, 5, 0.95); border-right: 1px solid #222; }
    .card-student { background: rgba(16, 30, 45, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(0, 255, 255, 0.2); border-radius: 16px; padding: 20px; text-align: center; }
    .id-name { font-size: 28px; font-weight: bold; margin: 12px 0; color: white; }
    .info-row { display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.1); padding: 8px 0; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] { background-color: rgba(20, 20, 20, 0.9); color: white; border: 1px solid #444; }
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
        req_cols = ['Name', 'Role', 'Spot Phone', 'Ticket_Number', 'Class', 'Entry_Status', 'Bus_Number', 'T_Shirt_Size', 'T_Shirt_Collected']
        for c in req_cols:
            if c not in df.columns: df[c] = 'N/A'
        return df.fillna("N/A")
    except: return pd.DataFrame()

def load_stock():
    try:
        df_s = conn.read(worksheet="Stock", ttl=0)
        return dict(zip(df_s['Size'], df_s['Quantity'].astype(int)))
    except: return {"S":0, "M":0, "L":0, "XL":0, "XXL":0}

if 'df' not in st.session_state: st.session_state.df = load_data()
if 'stock' not in st.session_state: st.session_state.stock = load_stock()

# ==================== 3. LOGIN ====================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.title("🔐 Willian's 26 | Admin")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u == "admin" and p == "1234": st.session_state.logged_in = True; st.rerun()
    st.stop()

# ==================== 4. MENU ====================
menu = st.sidebar.radio("Go To", ["🔍 Search & Entry", "➕ Add Staff/Teacher", "🚌 Bus Manager", "📊 Dashboard", "📝 Admin Data"])

# --- SEARCH & ENTRY ---
if menu == "🔍 Search & Entry":
    st.title("🔍 Search & Entry")
    q = st.text_input("🔎 Search by Ticket / Name / Phone:").strip()
    if q:
        df = st.session_state.df
        res = df[df['Name'].str.contains(q, case=False) | df['Ticket_Number'].str.contains(q, case=False)]
        if not res.empty:
            idx = res.index[0]; row = df.loc[idx]
            st.markdown(f'<div class="card-student"><div class="id-name">{row["Name"]}</div><div class="info-row"><span>Class</span><span>{row["Class"]}</span></div></div>', unsafe_allow_html=True)
            if st.button("✅ Confirm Entry"):
                st.session_state.df.at[idx, 'Entry_Status'] = 'Done'
                if safe_update("Data", st.session_state.df): st.success("Entry Recorded!"); st.rerun()

# --- BUS MANAGER (Class-wise Assign & PDF) ---
elif menu == "🚌 Bus Manager":
    st.title("🚌 Fleet & Class Assignment")
    buses = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    
    # Visual Stats
    cols = st.columns(4)
    for i, b in enumerate(buses):
        cnt = len(st.session_state.df[st.session_state.df['Bus_Number'] == b])
        cols[i].metric(b, f"{cnt}/{BUS_CAPACITY}", f"{BUS_CAPACITY-cnt} Seats")
        cols[i].progress(cnt/BUS_CAPACITY)

    st.markdown("---")
    
    # Class-wise Selection System
    st.subheader("🎯 Class-wise Selection")
    c1, c2, c3 = st.columns(3)
    sel_cls = c1.selectbox("Select Class", sorted(st.session_state.df['Class'].unique()))
    sel_bus = c2.selectbox("Select Target Bus", buses)
    
    if c3.button("🚀 Assign Class to Bus", use_container_width=True):
        mask = (st.session_state.df['Class'] == sel_cls) & (st.session_state.df['Bus_Number'] == 'Unassigned')
        eligible_indices = st.session_state.df[mask].index.tolist()
        
        current_bus_cnt = len(st.session_state.df[st.session_state.df['Bus_Number'] == sel_bus])
        available_seats = BUS_CAPACITY - current_bus_cnt
        
        if available_seats <= 0:
            st.error("Bus is already full!")
        else:
            to_assign = eligible_indices[:available_seats]
            for idx in to_assign:
                st.session_state.df.at[idx, 'Bus_Number'] = sel_bus
            
            if safe_update("Data", st.session_state.df):
                st.success(f"Assigned {len(to_assign)} students from {sel_cls} to {sel_bus}!")
                time.sleep(1); st.rerun()

    # PDF Output Section
    st.subheader("🖨️ Export PDF Manifest")
    if st.button("📄 Generate Print-Ready PDF"):
        html = """
        <html><head><style>
            body { font-family: sans-serif; padding: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #000; padding: 8px; text-align: left; }
            .bus-header { background: #f0f0f0; padding: 10px; margin-top: 30px; border-radius: 5px; }
            @media print { .page-break { page-break-after: always; } }
        </style></head><body>
        <h1 style='text-align:center;'>Official Bus Manifest - Willian's 26</h1>
        """
        for b in buses:
            b_df = st.session_state.df[st.session_state.df['Bus_Number'] == b]
            if not b_df.empty:
                html += f"<div class='bus-header'><h2>{b} - Total: {len(b_df)}</h2></div>"
                html += "<table><tr><th>SL</th><th>Name</th><th>Class</th><th>Phone</th><th>Signature</th></tr>"
                for i, (_, r) in enumerate(b_df.iterrows(), 1):
                    html += f"<tr><td>{i}</td><td>{r['Name']}</td><td>{r['Class']}</td><td>{r['Spot Phone']}</td><td>_______</td></tr>"
                html += "</table><div class='page-break'></div>"
        html += "</body></html>"
        st.download_button("⬇️ Download PDF Ready File", html, "Bus_Manifest.html", "text/html")

# --- DASHBOARD (Remaining Stock Section) ---
elif menu == "📊 Dashboard":
    st.title("📊 Event Analytics")
    
    # Stock Remaining Section
    st.subheader("👕 T-Shirt Inventory (Remaining)")
    s_cols = st.columns(5)
    for i, (sz, qty) in enumerate(st.session_state.stock.items()):
        # গণনা করুন কতজন অলরেডি নিয়েছে
        taken = len(st.session_state.df[(st.session_state.df['T_Shirt_Size'] == sz) & (st.session_state.df['T_Shirt_Collected'] == 'Yes')])
        remain = qty - taken
        color = "normal" if remain > 5 else "inverse"
        s_cols[i].metric(f"Size {sz}", f"{remain} Left", f"Total: {qty}", delta_color=color)

    st.markdown("---")
    
    # Entry Stats
    c1, c2 = st.columns(2)
    total = len(st.session_state.df)
    entered = len(st.session_state.df[st.session_state.df['Entry_Status'] == 'Done'])
    c1.metric("Total Attendance", f"{entered}/{total}")
    c2.progress(entered/total if total > 0 else 0)

# --- ADMIN DATA ---
elif menu == "📝 Admin Data":
    st.title("📝 Full Database")
    st.dataframe(st.session_state.df, use_container_width=True)
    st.download_button("CSV Export", st.session_state.df.to_csv(), "full_data.csv")

# ==================== CREDITS ====================
st.sidebar.markdown("---")
st.sidebar.caption("System by Gemini AI | CineMotion")
