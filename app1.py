import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time
import streamlit.components.v1 as components

# ==================== 1. CONFIG & ULTRA PREMIUM STYLE ====================
st.set_page_config(page_title="Event OS Pro | Willian's 26", page_icon="🎆", layout="wide")

st.markdown("""
    <style>
    /* background */
    .stApp {
        background-color: #000000;
        background-image: linear-gradient(rgba(0, 0, 0, 0.85), rgba(0, 0, 0, 0.95)),
            url("https://images.unsplash.com/photo-1470225620780-dba8ba36b745?q=80&w=2070&auto=format&fit=crop");
        background-size: cover; background-attachment: fixed; color: #ffffff;
    }
    
    /* Premium Cards */
    .card-student {
        background: rgba(16, 30, 45, 0.7); backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 255, 255, 0.2); border-radius: 16px;
        padding: 25px; text-align: center; margin-bottom: 20px;
    }
    .id-name { font-size: 30px; font-weight: bold; color: #00ffff; text-shadow: 0 0 10px rgba(0,255,255,0.5); }
    .info-row { display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.1); padding: 10px 0; font-size: 15px; }
    
    /* Input & Select Box Styling */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(30, 30, 30, 0.9) !important; color: white !important; border: 1px solid #444 !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: rgba(5, 5, 5, 0.98); border-right: 1px solid #333; }
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
    try:
        df = conn.read(worksheet="Data", ttl=0)
        # Ensure columns exist
        cols = ['Name', 'Role', 'Spot Phone', 'Ticket_Number', 'Class', 'Entry_Status', 'Bus_Number', 'T_Shirt_Size', 'T_Shirt_Collected']
        for c in cols:
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

# ==================== 3. LOGIN & TIMER ====================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.title("🔐 Willian's 26 | Admin Portal")
    u, p = st.columns(2)
    user = u.text_input("Username")
    pas = p.text_input("Password", type="password")
    if st.button("Access System"):
        if user == "admin" and pas == "1234": st.session_state.logged_in = True; st.rerun()
    st.stop()

# --- TIMER COMPONENT ---
timer_html = """<div style="background: linear-gradient(135deg, #000428, #004e92); color: white; padding: 15px; border-radius: 12px; text-align: center; border: 1px solid #00ff88;">
<div style="font-size: 10px; letter-spacing: 2px;">EVENT STARTING IN</div><div style="font-size: 24px; font-weight: bold; color: #00ff88;">3RD FEB 2026</div></div>"""
with st.sidebar: components.html(timer_html, height=100)

menu = st.sidebar.radio("Navigation", ["🔍 Search & Entry", "🚌 Bus Manager", "📊 Dashboard", "📝 Admin Data"])

# ==================== 4. FEATURES ====================

# --- SEARCH & ENTRY ---
if menu == "🔍 Search & Entry":
    st.title("🔍 Search & Entry")
    q = st.text_input("Enter Ticket, Name or Phone:").strip()
    if q:
        res = st.session_state.df[st.session_state.df['Name'].str.contains(q, case=False) | st.session_state.df['Ticket_Number'].str.contains(q, case=False)]
        if not res.empty:
            idx = res.index[0]; row = st.session_state.df.loc[idx]
            st.markdown(f"""<div class="card-student">
                <div class="id-name">{row['Name']}</div>
                <div class="info-row"><span>Ticket</span><span>{row['Ticket_Number']}</span></div>
                <div class="info-row"><span>Class</span><span>{row['Class']}</span></div>
                <div class="info-row"><span>Bus</span><span>{row['Bus_Number']}</span></div>
                <div class="info-row"><span>Entry Status</span><span>{row['Entry_Status']}</span></div>
            </div>""", unsafe_allow_html=True)
            if st.button("🚀 Confirm Entry"):
                st.session_state.df.at[idx, 'Entry_Status'] = 'Done'
                if safe_update("Data", st.session_state.df): st.success("Entry Marked!"); time.sleep(1); st.rerun()
        else: st.warning("No Record Found.")

# --- BUS MANAGER (CLASS WISE SELECTION & PDF) ---
elif menu == "🚌 Bus Manager":
    st.title("🚌 Bus & Fleet Manager")
    buses = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    
    # Bus Capacity Progress
    c = st.columns(4)
    for i, b in enumerate(buses):
        count = len(st.session_state.df[st.session_state.df['Bus_Number'] == b])
        c[i].metric(b, f"{count}/{BUS_CAPACITY}", f"{BUS_CAPACITY-count} Seats Left")
        c[i].progress(count/BUS_CAPACITY)

    st.markdown("---")
    
    # CLASS WISE BUS ASSIGNMENT
    st.subheader("🎯 Class-wise Bus Assignment")
    col1, col2, col3 = st.columns(3)
    target_class = col1.selectbox("Choose Class", sorted(st.session_state.df['Class'].unique()))
    target_bus = col2.selectbox("Assign to Bus", buses)
    
    if col3.button("Confirm Batch Assignment", use_container_width=True):
        # Filter students of that class who are unassigned
        mask = (st.session_state.df['Class'] == target_class) & (st.session_state.df['Bus_Number'] == 'Unassigned')
        student_indices = st.session_state.df[mask].index.tolist()
        
        current_bus_fill = len(st.session_state.df[st.session_state.df['Bus_Number'] == target_bus])
        seats_left = BUS_CAPACITY - current_bus_fill
        
        if seats_left <= 0:
            st.error("Target Bus is already full!")
        elif not student_indices:
            st.warning(f"No unassigned students left in {target_class}")
        else:
            to_assign = student_indices[:seats_left]
            for idx in to_assign:
                st.session_state.df.at[idx, 'Bus_Number'] = target_bus
            
            if safe_update("Data", st.session_state.df):
                st.success(f"Successfully moved {len(to_assign)} students from {target_class} to {target_bus}!")
                st.rerun()

    # PDF EXPORT SECTION
    st.markdown("---")
    st.subheader("🖨️ Export Bus Manifest")
    if st.button("📄 Generate Print-Ready PDF Manifest"):
        html_manifest = """
        <html><head><style>
            body { font-family: 'Segoe UI', sans-serif; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 50px; }
            th, td { border: 1px solid #333; padding: 10px; text-align: left; }
            th { background-color: #f2f2f2; }
            h2 { color: #004e92; border-bottom: 2px solid #004e92; }
            @media print { .page-break { page-break-after: always; } }
        </style></head><body>
        <h1 style='text-align:center;'>Willian's 26 - Bus Passenger List</h1>
        """
        for b in buses:
            b_list = st.session_state.df[st.session_state.df['Bus_Number'] == b]
            if not b_list.empty:
                html_manifest += f"<h2>{b} - Total: {len(b_list)}</h2>"
                html_manifest += "<table><tr><th>SL</th><th>Name</th><th>Class</th><th>Phone</th><th>Sign</th></tr>"
                for i, (_, row) in enumerate(b_list.iterrows(), 1):
                    html_manifest += f"<tr><td>{i}</td><td>{row['Name']}</td><td>{row['Class']}</td><td>{row['Spot Phone']}</td><td></td></tr>"
                html_manifest += "</table><div class='page-break'></div>"
        
        html_manifest += "</body></html>"
        st.download_button("⬇️ Download PDF (HTML Format)", html_manifest, "Bus_Manifest.html", "text/html")

# --- DASHBOARD (REMAINING STOCK) ---
elif menu == "📊 Dashboard":
    st.title("📊 Event Statistics & Inventory")
    
    # 👕 REMAINING STOCK CALCULATION
    st.subheader("👕 T-Shirt Stock Status (Remaining)")
    st_cols = st.columns(5)
    for i, (size, total_qty) in enumerate(st.session_state.stock.items()):
        # Calculate how many collected
        collected = len(st.session_state.df[(st.session_state.df['T_Shirt_Size'] == size) & (st.session_state.df['T_Shirt_Collected'] == 'Yes')])
        remaining = total_qty - collected
        
        with st_cols[i]:
            st.metric(label=f"Size {size}", value=f"{remaining} Left", delta=f"Total: {total_qty}", delta_color="off")
            st.progress(max(0, min(remaining/total_qty, 1.0)) if total_qty > 0 else 0)

    st.markdown("---")
    # Entry Stats
    total = len(st.session_state.df)
    done = len(st.session_state.df[st.session_state.df['Entry_Status'] == 'Done'])
    st.metric("Total Check-ins", f"{done} / {total}", f"{total-done} Pending")

# --- ADMIN DATA ---
elif menu == "📝 Admin Data":
    st.title("📝 Data Management")
    st.dataframe(st.session_state.df, use_container_width=True)
    st.download_button("Download CSV", st.session_state.df.to_csv(index=False), "event_data.csv")
