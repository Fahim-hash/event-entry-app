import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time
import pytz
import streamlit.components.v1 as components

# ==============================================================================
# 1. CONFIGURATION & ADVANCED CSS (NO SHORTCUTS)
# ==============================================================================
st.set_page_config(
    page_title="Event OS Pro | Willian's 26 | Management Suite", 
    page_icon="🎆", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* 🔥 ULTRA PREMIUM UI 🔥 */
    .stApp {
        background-color: #000000;
        background-image: linear-gradient(rgba(0, 0, 0, 0.92), rgba(0, 0, 0, 0.96)),
            url("https://images.unsplash.com/photo-1470225620780-dba8ba36b745?q=80&w=2070&auto=format&fit=crop");
        background-size: cover; background-attachment: fixed; color: #ffffff;
    }
    
    section[data-testid="stSidebar"] {
        background-color: rgba(5, 5, 5, 0.98);
        border-right: 1px solid #333;
    }

    /* ALL ORIGINAL PREMIUM CARDS RESTORED IN FULL DETAIL */
    .card-student {
        background: rgba(16, 30, 45, 0.75); backdrop-filter: blur(15px);
        border: 1px solid rgba(0, 255, 255, 0.3); border-radius: 20px; 
        padding: 25px; text-align: center; margin-bottom: 25px;
        box-shadow: 0 8px 32px 0 rgba(0, 255, 255, 0.1);
    }
    
    @keyframes pulse-glow {
        0% { box-shadow: 0 0 5px rgba(213, 0, 249, 0.4); }
        50% { box-shadow: 0 0 25px rgba(213, 0, 249, 0.7); }
        100% { box-shadow: 0 0 5px rgba(213, 0, 249, 0.4); }
    }
    .card-organizer {
        background: linear-gradient(135deg, rgba(40, 0, 80, 0.8), rgba(10, 0, 20, 0.9));
        border: 2px solid #d500f9; border-radius: 20px; 
        padding: 25px; text-align: center; animation: pulse-glow 3s infinite;
    }

    .card-staff {
        background: linear-gradient(145deg, #002b20, #001a13);
        border-left: 5px solid #00ff88; border-radius: 20px; 
        padding: 25px; text-align: center;
    }

    .card-elite {
        background: linear-gradient(160deg, #111 0%, #222 100%);
        border: 2px solid #ffd700; box-shadow: 0 0 30px rgba(255, 215, 0, 0.3);
        padding: 30px; text-align: center; position: relative;
    }
    .card-elite::after {
        content: "⭐ VIP ACCESS ⭐"; position: absolute; top: 0; left: 50%; transform: translateX(-50%);
        background: #ffd700; color: #000; font-weight: 900; font-size: 10px; padding: 3px 15px; border-radius: 0 0 10px 10px;
    }

    /* ID CARD TEXT ELEMENTS */
    .id-name { font-size: 32px; font-weight: 800; margin: 15px 0; color: #fff; }
    .role-badge { 
        display: inline-block; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2);
        padding: 5px 20px; border-radius: 50px; font-size: 12px; font-weight: bold; text-transform: uppercase;
    }
    .info-row { 
        display: flex; justify-content: space-between; align-items: center;
        padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.08); font-size: 15px; color: #ddd;
    }

    /* FORMS & INPUTS */
    .stTextInput input { border-radius: 10px !important; background: #111 !important; color: #00ff88 !important; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. CORE DATA ENGINE (DETAILED SYNC)
# ==============================================================================
conn = st.connection("gsheets", type=GSheetsConnection)
BUS_CAPACITY = 45

def get_dhaka_time():
    return datetime.now(pytz.timezone('Asia/Dhaka')).strftime("%H:%M:%S")

def sync_data(ws, df):
    try:
        conn.update(worksheet=ws, data=df)
        return True
    except Exception as e:
        st.error(f"Sync Failure: {e}")
        return False

def load_master_df():
    try:
        df = conn.read(worksheet="Data", ttl=0)
        # Ensure every column from original 463-line version exists
        cols = ['Name', 'Role', 'Spot Phone', 'Guardian Phone', 'Ticket_Number', 'Class', 'Roll', 'Entry_Status', 'Entry_Time', 'Bus_Number', 'T_Shirt_Size', 'T_Shirt_Collected', 'Notes']
        for c in cols:
            if c not in df.columns: df[c] = 'N/A'
        return df.fillna("N/A").astype(str)
    except: return pd.DataFrame()

def load_stock_dict():
    try:
        df_s = conn.read(worksheet="Stock", ttl=0)
        return dict(zip(df_s['Size'], df_s['Quantity'].astype(int)))
    except: return {"S":0, "M":0, "L":0, "XL":0, "XXL":0}

if 'df' not in st.session_state: st.session_state.df = load_master_df()
if 'stock' not in st.session_state: st.session_state.stock = load_stock_dict()

# ==============================================================================
# 3. AUTHENTICATION & SIDEBAR TIMER
# ==============================================================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.title("🔐 Secure Access Portal")
    u, p = st.text_input("Admin ID"), st.text_input("Access Key", type="password")
    if st.button("AUTHENTICATE", type="primary"):
        if u == "admin" and p == "1234": st.session_state.logged_in = True; st.rerun()
    st.stop()

with st.sidebar:
    st.markdown("<h3 style='color:#00ff88;'>⚡ COMMAND CENTER</h3>", unsafe_allow_html=True)
    
    # --- UPGRADED LIVE TIMER ---
    target = datetime(2026, 2, 3, 9, 0, 0)
    diff = target - datetime.now()
    d, h, m, s = diff.days, diff.seconds//3600, (diff.seconds//60)%60, diff.seconds%60
    
    timer_html = f"""
    <div style="background: #0f0f0f; border: 1px solid #00ff88; padding: 15px; border-radius: 15px; text-align: center;">
        <div style="color: #00ff88; font-size: 10px; letter-spacing: 2px;">COUNTDOWN</div>
        <div style="display: flex; justify-content: space-around; margin-top: 10px;">
            <div><b style="font-size:18px;">{d:02d}</b><br><small>DAYS</small></div>
            <div><b style="font-size:18px;">{h:02d}</b><br><small>HRS</small></div>
            <div><b style="font-size:18px;">{m:02d}</b><br><small>MIN</small></div>
            <div><b style="font-size:18px; color:#ff4b4b;">{s:02d}</b><br><small>SEC</small></div>
        </div>
    </div>
    """
    components.html(timer_html, height=120)
    
    nav = st.sidebar.radio("NAVIGATE", ["🔍 Search & Entry", "➕ Add Entry", "🚌 Bus Manager", "📊 Dashboard", "📝 Database Master"])
    if st.button("🔄 SYNC CLOUD"): 
        st.session_state.df = load_master_df()
        st.session_state.stock = load_stock_dict()
        st.rerun()

# ==============================================================================
# 4. MODULE: SEARCH & DETAILED EDITOR (RESTORED FULL LOGIC)
# ==============================================================================
if nav == "🔍 Search & Entry":
    st.title("🔍 Search & Management")
    query = st.text_input("🔎 Search by Ticket / Name / Phone:").strip()
    
    if query:
        res = st.session_state.df[st.session_state.df['Name'].str.contains(query, case=False) | st.session_state.df['Ticket_Number'].str.contains(query, case=False) | st.session_state.df['Spot Phone'].str.contains(query, case=False)]
        
        if not res.empty:
            idx = res.index[0]; row = st.session_state.df.loc[idx]
            
            # Detailed Role Sorting
            role = row['Role']
            if role in ["Principal", "College Head"]: c_cls = "card-elite"
            elif role == "Organizer": c_cls = "card-organizer"
            elif role in ["Teacher", "Staff"]: c_cls = "card-staff"
            else: c_cls = "card-student"

            col1, col2 = st.columns([1, 1.8])
            with col1:
                st.markdown(f"""<div class="{c_cls}">
                    <div class="role-badge">{role}</div>
                    <div class="id-name">{row['Name']}</div>
                    <div class="info-row"><span>Ticket</span><span>{row['Ticket_Number']}</span></div>
                    <div class="info-row"><span>Class</span><span>{row['Class']}</span></div>
                    <div class="info-row"><span>Bus</span><span>{row['Bus_Number']}</span></div>
                    <div style="margin-top:20px; font-weight:bold; color:{'#00ff88' if row['Entry_Status']=='Done' else '#ff4b4b'};">
                        {'✅ CHECKED IN' if row['Entry_Status']=='Done' else '⏳ PENDING'}
                    </div>
                </div>""", unsafe_allow_html=True)
            
            with col2:
                with st.container(border=True):
                    st.subheader("✏️ Detailed Record Editor")
                    # EVERY SINGLE INPUT FROM 463-LINE VERSION RESTORED
                    ed_name = st.text_input("Name", row['Name'])
                    c_a, c_b = st.columns(2)
                    ed_phone = c_a.text_input("Phone", row['Spot Phone'])
                    ed_guardian = c_b.text_input("Guardian", row['Guardian Phone'])
                    
                    c_c, c_d, c_e = st.columns(3)
                    role_opts = ["Student", "Volunteer", "Teacher", "Staff", "Organizer", "Principal"]
                    ed_role = c_c.selectbox("Role", role_opts, index=role_opts.index(role) if role in role_opts else 0)
                    ed_class = c_d.text_input("Class", row['Class'])
                    ed_ticket = c_e.text_input("Ticket #", row['Ticket_Number'])
                    
                    c_f, c_g = st.columns(2)
                    sz_opts = ["S", "M", "L", "XL", "XXL"]
                    ed_size = c_f.selectbox("T-Shirt", sz_opts, index=sz_opts.index(row['T_Shirt_Size']) if row['T_Shirt_Size'] in sz_opts else 2)
                    bus_opts = ["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"]
                    ed_bus = c_g.selectbox("Bus Assign", bus_opts, index=bus_opts.index(row['Bus_Number']) if row['Bus_Number'] in bus_opts else 0)
                    
                    st.markdown("---")
                    ed_ent = st.toggle("Confirm Entry", row['Entry_Status'] == 'Done')
                    ed_kit = st.toggle("Confirm Kit Collection", row['T_Shirt_Collected'] == 'Yes')

                    if st.button("💾 SAVE MASTER UPDATE", type="primary", use_container_width=True):
                        st.session_state.df.at[idx, 'Name'] = ed_name
                        st.session_state.df.at[idx, 'Spot Phone'] = ed_phone
                        st.session_state.df.at[idx, 'Guardian Phone'] = ed_guardian
                        st.session_state.df.at[idx, 'Role'] = ed_role
                        st.session_state.df.at[idx, 'Class'] = ed_class
                        st.session_state.df.at[idx, 'Ticket_Number'] = ed_ticket
                        st.session_state.df.at[idx, 'T_Shirt_Size'] = ed_size
                        st.session_state.df.at[idx, 'Bus_Number'] = ed_bus
                        st.session_state.df.at[idx, 'Entry_Status'] = 'Done' if ed_ent else 'N/A'
                        st.session_state.df.at[idx, 'T_Shirt_Collected'] = 'Yes' if ed_kit else 'No'
                        
                        if ed_ent and row['Entry_Time'] == 'N/A':
                            st.session_state.df.at[idx, 'Entry_Time'] = get_dhaka_time()
                        
                        if sync_data("Data", st.session_state.df):
                            st.success("Cloud Synchronized!"); time.sleep(0.5); st.rerun()

# ==============================================================================
# 5. MODULE: DETAILED BUS MANAGER (BULK ASSIGN + PDF)
# ==============================================================================
elif nav == "🚌 Bus Manager":
    st.title("🚌 Fleet & Class Operations")
    
    # 1. LIVE SEAT TRACKER
    st.subheader("📊 Occupancy Monitor")
    buses = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    m_cols = st.columns(4)
    for i, b in enumerate(buses):
        count = len(st.session_state.df[st.session_state.df['Bus_Number'] == b])
        m_cols[i].metric(b, f"{count}/{BUS_CAPACITY}", f"{BUS_CAPACITY-count} Left")
        m_cols[i].progress(min(count/BUS_CAPACITY, 1.0))

    # 2. BULK ASSIGN SYSTEM (NEW)
    st.markdown("---")
    st.subheader("🎯 Class-wise Bulk Assignment")
    classes = sorted([c for c in st.session_state.df['Class'].unique() if c != 'N/A'])
    
    bc1, bc2, bc3 = st.columns(3)
    sel_cls = bc1.selectbox("Target Class", classes)
    sel_bus = bc2.selectbox("Destination Bus", buses)
    
    unassigned = st.session_state.df[(st.session_state.df['Class'] == sel_cls) & (st.session_state.df['Bus_Number'] == 'Unassigned')]
    
    if bc3.button(f"MOVE {len(unassigned)} STUDENTS", use_container_width=True):
        seats = BUS_CAPACITY - len(st.session_state.df[st.session_state.df['Bus_Number'] == sel_bus])
        if seats > 0:
            to_move = unassigned.index[:seats]
            for i in to_move: st.session_state.df.at[i, 'Bus_Number'] = sel_bus
            if sync_data("Data", st.session_state.df):
                st.success(f"Deployed {len(to_move)} from {sel_cls}!"); time.sleep(1); st.rerun()
        else: st.error("Bus is Full!")

    # 3. PDF MANIFEST
    st.markdown("---")
    if st.button("📄 GENERATE PRINTABLE MANIFEST"):
        html = "<html><head><style>table{width:100%; border-collapse:collapse;} th,td{border:1px solid #000; padding:8px;}</style></head><body>"
        for b in buses:
            passengers = st.session_state.df[st.session_state.df['Bus_Number'] == b]
            if not passengers.empty:
                html += f"<h2>{b} List</h2><table><tr><th>SL</th><th>Name</th><th>Class</th><th>Phone</th></tr>"
                for i, (_, r) in enumerate(passengers.iterrows(), 1):
                    html += f"<tr><td>{i}</td><td>{r['Name']}</td><td>{r['Class']}</td><td>{r['Spot Phone']}</td></tr>"
                html += "</table><br>"
        html += "</body></html>"
        st.download_button("⬇️ DOWNLOAD MANIFEST", html, "Manifest.html", "text/html")

# ==============================================================================
# 6. MODULE: STRATEGIC DASHBOARD (STOCK CHECKER)
# ==============================================================================
elif nav == "📊 Dashboard":
    st.title("📊 Mission Intelligence")
    
    # --- DETAILED T-SHIRT STOCK CHECKER ---
    st.subheader("👕 T-Shirt Strategic Inventory")
    sc = st.columns(5)
    for i, (size, total) in enumerate(st.session_state.stock.items()):
        taken = len(st.session_state.df[(st.session_state.df['T_Shirt_Size'] == size) & (st.session_state.df['T_Shirt_Collected'] == 'Yes')])
        rem = total - taken
        with sc[i]:
            st.markdown(f"""<div style='background:rgba(255,255,255,0.05); padding:10px; border-radius:10px; border:1px solid {"#00ff88" if rem>5 else "#ff4b4b"}; text-align:center;'>
                <small>{size}</small><br><b style='font-size:20px;'>{rem}</b><br><small>Left</small>
            </div>""", unsafe_allow_html=True)
            st.progress(max(0, min(rem/total, 1.0)) if total > 0 else 0)

    # MASTER STATS
    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Registered", len(st.session_state.df))
    m2.metric("Checked-in", len(st.session_state.df[st.session_state.df['Entry_Status'] == 'Done']))
    m3.metric("Kits Delivered", len(st.session_state.df[st.session_state.df['T_Shirt_Collected'] == 'Yes']))

# ==============================================================================
# 7. MODULE: ADD ENTRY & DATABASE MASTER
# ==============================================================================
elif nav == "➕ Add Entry":
    st.title("➕ Manual Database Entry")
    with st.form("add_form"):
        n = st.text_input("Full Name")
        r = st.selectbox("Role", ["Student", "Volunteer", "Teacher", "Staff"])
        p = st.text_input("Phone")
        c = st.text_input("Class")
        if st.form_submit_button("ADD TO CLOUD"):
            new = {'Name': n, 'Role': r, 'Spot Phone': p, 'Class': c, 'Ticket_Number': f"MAN-{int(time.time())}", 'Bus_Number': 'Unassigned', 'T_Shirt_Collected': 'No', 'T_Shirt_Size': 'L', 'Entry_Status': 'N/A'}
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new])], ignore_index=True)
            if sync_data("Data", st.session_state.df): st.success("Added!"); st.rerun()

elif nav == "📝 Database Master":
    st.title("📝 Master Control")
    st.dataframe(st.session_state.df, use_container_width=True)
    st.download_button("📥 EXPORT CSV", st.session_state.df.to_csv(index=False), "master.csv")
