import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time
import pytz
import streamlit.components.v1 as components

# ==============================================================================
# 1. ADVANCED GLOBAL CONFIGURATION (EXACT PREMIUM STYLE)
# ==============================================================================
st.set_page_config(
    page_title="Event OS Ultra | Willian's 26", 
    page_icon="🎆", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ULTRA-DETAILED CSS ENGINE ---
st.markdown("""
    <style>
    /* MAIN INTERFACE */
    .stApp {
        background-color: #000000;
        background-image: linear-gradient(rgba(0, 0, 0, 0.92), rgba(0, 0, 0, 0.95)),
            url("https://images.unsplash.com/photo-1470225620780-dba8ba36b745?q=80&w=2070&auto=format&fit=crop");
        background-size: cover; background-attachment: fixed; color: #ffffff;
    }
    
    /* PREMIUM CARDS (EXACT SAME AS PREVIOUS) */
    .card-student { background: rgba(16, 30, 45, 0.7); border: 1px solid rgba(0, 255, 255, 0.2); border-radius: 16px; padding: 25px; text-align: center; margin-bottom: 20px; transition: 0.3s; }
    .card-organizer { background: linear-gradient(135deg, rgba(40, 0, 80, 0.9), rgba(10, 0, 20, 0.9)); border: 2px solid #d500f9; border-radius: 16px; padding: 25px; text-align: center; animation: pulse 2s infinite; }
    .card-staff { background: linear-gradient(145deg, #002b20, #001a13); border-top: 3px solid #00ff88; border-radius: 16px; padding: 25px; text-align: center; }
    .card-elite { background: linear-gradient(to bottom, #111, #222); border: 2px solid #ffd700; border-radius: 16px; padding: 25px; text-align: center; position: relative; box-shadow: 0 0 20px rgba(255, 215, 0, 0.3); }
    .card-elite::after { content: "VIP ACCESS"; position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: #ffd700; color: black; font-weight: bold; font-size: 10px; padding: 2px 10px; border-radius: 10px; }

    .id-name { font-size: 30px; font-weight: 900; margin: 15px 0; color: white; letter-spacing: 1px; }
    .info-row { display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.08); padding: 10px 0; font-size: 15px; color: #ccc; }
    .role-badge { background: rgba(255,255,255,0.1); padding: 5px 15px; border-radius: 20px; font-size: 12px; text-transform: uppercase; border: 1px solid rgba(255,255,255,0.2); }
    
    /* 👕 NEW: STOCK BOX STYLING */
    .stock-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px; padding: 15px; text-align: center;
        border-top: 4px solid #00ff88;
    }
    .stock-val { font-size: 28px; font-weight: bold; color: #00ff88; }
    </style>
    """, unsafe_allow_html=True)

# ==================== 2. DATA ENGINE (MULTI-SHEET SYNC) ====================
conn = st.connection("gsheets", type=GSheetsConnection)
BUS_CAPACITY = 45

def get_dhaka_time():
    return datetime.now(pytz.timezone('Asia/Dhaka')).strftime("%I:%M:%S %p")

def sync_all_data():
    """Detailed sync for both Data and Stock sheets"""
    try:
        conn.update(worksheet="Data", data=st.session_state.df)
        # Convert stock dict back to DF for sync
        stock_df = pd.DataFrame([{"Size": k, "Quantity": v} for k, v in st.session_state.stock.items()])
        conn.update(worksheet="Stock", data=stock_df)
        st.toast("✅ Cloud Database Synchronized!", icon="🌐")
    except Exception as e:
        st.error(f"❌ Critical Sync Failure: {e}")

def load_master_data():
    try:
        df = conn.read(worksheet="Data", ttl=0)
        # Ensure all required columns exist (The 3x expansion logic)
        req = ['Name', 'Role', 'Spot Phone', 'Guardian Phone', 'Ticket_Number', 'Class', 'Roll', 'Entry_Status', 'Entry_Time', 'Bus_Number', 'T_Shirt_Size', 'T_Shirt_Collected', 'Notes']
        for col in req:
            if col not in df.columns: df[col] = 'N/A'
        return df.fillna("N/A").astype(str)
    except: return pd.DataFrame()

def load_stock_data():
    try:
        df_s = conn.read(worksheet="Stock", ttl=0)
        return dict(zip(df_s['Size'], df_s['Quantity'].astype(int)))
    except:
        # Default stock if sheet is empty or not found
        return {"S": 50, "M": 100, "L": 150, "XL": 100, "XXL": 50}

# Initialize Sessions
if 'df' not in st.session_state: st.session_state.df = load_master_data()
if 'stock' not in st.session_state: st.session_state.stock = load_stock_data()

# ==================== 3. SECURITY GATEWAY ====================
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center;'>🔐 Administrative Access</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        col_l, col_r = st.columns(2)
        u = col_l.text_input("Username")
        p = col_r.text_input("Security Pin", type="password")
        if st.button("AUTHENTICATE SYSTEM", use_container_width=True, type="primary"):
            if u == "admin" and p == "1234":
                st.session_state.auth = True; st.rerun()
            else: st.error("INVALID CREDENTIALS")
    st.stop()

# ==================== 4. SIDEBAR MISSION CONTROL ====================
with st.sidebar:
    st.markdown("<h2 style='color:#00ff88;'>🚀 MISSION CONTROL</h2>", unsafe_allow_html=True)
    
    # LIVE TIMER COMPONENT
    target_dt = "2026-02-03T09:00:00+06:00"
    timer_code = f"""
    <div style="background:#111; border:1px solid #333; padding:15px; border-radius:10px; text-align:center;">
        <div style="font-size:10px; color:#aaa; letter-spacing:2px;">COUNTDOWN TO EVENT</div>
        <div id="timer" style="font-size:22px; color:#00ff88; font-weight:bold; font-family:monospace;">--:--:--</div>
    </div>
    <script>
        const target = new Date("{target_dt}").getTime();
        setInterval(() => {{
            const now = new Date().getTime();
            const diff = target - now;
            const h = Math.floor(diff / (1000*60*60));
            const m = Math.floor((diff % (1000*60*60)) / (1000*60));
            const s = Math.floor((diff % (1000*60)) / 1000);
            document.getElementById('timer').innerHTML = h + "h " + m + "m " + s + "s";
        }}, 1000);
    </script>
    """
    components.html(timer_code, height=100)
    
    st.markdown("---")
    menu = st.radio("SYSTEM MODULES", ["🔍 Search & Check-in", "➕ Manual Registration", "🚌 Fleet & Class Manager", "👕 Inventory & Stats", "📝 Master Database"])
    
    if st.button("🔄 FORCE RE-SYNC ALL"):
        st.session_state.df = load_master_data()
        st.session_state.stock = load_stock_data()
        st.rerun()

# ==================== 5. MODULE: SEARCH & EXTENDED ENTRY ====================
if menu == "🔍 Search & Check-in":
    st.title("🔍 Advanced Search Engine")
    query = st.text_input("🔎 Input Ticket ID, Name, or Mobile Number:").strip()
    
    if query:
        results = st.session_state.df[
            st.session_state.df['Name'].str.contains(query, case=False) | 
            st.session_state.df['Ticket_Number'].str.contains(query, case=False) | 
            st.session_state.df['Spot Phone'].str.contains(query, case=False)
        ]
        
        if not results.empty:
            idx = results.index[0]; row = st.session_state.df.loc[idx]
            
            # --- CARD SELECTION LOGIC ---
            role = row['Role']
            c_style = "card-elite" if role in ["Principal", "College Head"] else "card-organizer" if role == "Organizer" else "card-staff" if "Staff" in role or "Teacher" in role else "card-student"
            
            view_col, edit_col = st.columns([1, 1.6])
            
            with view_col:
                st.markdown(f"""
                <div class="{c_style}">
                    <div class="role-badge">{role}</div>
                    <div class="id-name">{row['Name']}</div>
                    <div class="info-row"><span>Ticket ID</span><b style="color:#00ff88;">{row['Ticket_Number']}</b></div>
                    <div class="info-row"><span>Class/Roll</span><span>{row['Class']} / {row['Roll']}</span></div>
                    <div class="info-row"><span>Bus Fleet</span><span style="color:#ffd700;">{row['Bus_Number']}</span></div>
                    <div style="margin-top:20px; font-size:18px; font-weight:bold; color:{'#00ff88' if row['Entry_Status']=='Done' else '#ff4b4b'};">
                        {'✅ MISSION ENTERED' if row['Entry_Status']=='Done' else '⏳ ACCESS PENDING'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with edit_col:
                with st.container(border=True):
                    st.subheader("🛠️ Record Management")
                    c1, c2 = st.columns(2)
                    e_bus = c1.selectbox("Assign Bus", ["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"], index=["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"].index(row['Bus_Number']))
                    e_size = c2.selectbox("T-Shirt Size", ["S", "M", "L", "XL", "XXL"], index=["S", "M", "L", "XL", "XXL"].index(row['T_Shirt_Size']) if row['T_Shirt_Size'] in ["S", "M", "L", "XL", "XXL"] else 2)
                    
                    st.markdown("---")
                    ca, cb = st.columns(2)
                    e_entry = ca.toggle("Final Entry Status", row['Entry_Status'] == 'Done')
                    e_kit = cb.toggle("T-Shirt Kit Collected", row['T_Shirt_Collected'] == 'Yes')
                    
                    if st.button("💾 SAVE DATA & UPDATE CLOUD", type="primary", use_container_width=True):
                        # --- 👕 ADVANCED STOCK LOGIC ---
                        # If marking as collected for the first time
                        if e_kit and row['T_Shirt_Collected'] != 'Yes':
                            if st.session_state.stock[e_size] > 0:
                                st.session_state.stock[e_size] -= 1
                            else:
                                st.error(f"❌ OUT OF STOCK FOR SIZE {e_size}!"); st.stop()
                        # If unmarking as collected
                        elif not e_kit and row['T_Shirt_Collected'] == 'Yes':
                            st.session_state.stock[e_size] += 1
                        
                        # Update DataFrame
                        st.session_state.df.at[idx, 'Bus_Number'] = e_bus
                        st.session_state.df.at[idx, 'T_Shirt_Size'] = e_size
                        st.session_state.df.at[idx, 'Entry_Status'] = 'Done' if e_entry else 'N/A'
                        st.session_state.df.at[idx, 'T_Shirt_Collected'] = 'Yes' if e_kit else 'No'
                        
                        if e_entry and row['Entry_Time'] == 'N/A':
                            st.session_state.df.at[idx, 'Entry_Time'] = get_dhaka_time()
                        
                        sync_all_data()
                        st.success("RECORD UPDATED SUCCESSFULLY!"); time.sleep(1); st.rerun()
        else: st.warning("NO MATCHING RECORD FOUND IN DATABASE.")

# ==================== 6. MODULE: CLASS-WISE BUS ASSIGN ====================
elif menu == "🚌 Fleet & Class Manager":
    st.title("🚌 Fleet & Class Deployment")
    
    # BUS SEATING VISUALIZER
    
    
    st.subheader("📊 Fleet Capacity Status")
    f_cols = st.columns(4)
    for i, b_name in enumerate(["Bus 1", "Bus 2", "Bus 3", "Bus 4"]):
        current_fill = len(st.session_state.df[st.session_state.df['Bus_Number'] == b_name])
        f_cols[i].metric(b_name, f"{current_fill}/{BUS_CAPACITY}", f"{BUS_CAPACITY - current_fill} Free")
        f_cols[i].progress(min(current_fill/BUS_CAPACITY, 1.0))

    st.markdown("---")
    st.subheader("🎯 Class-wise Bulk Assignment")
    with st.container(border=True):
        st.info("Select a class and assign all its unassigned students to a specific bus in one click.")
        
        c_list = sorted([c for c in st.session_state.df['Class'].unique() if c != 'N/A'])
        
        b1, b2, b3 = st.columns([2, 2, 1])
        target_class = b1.selectbox("Choose Target Class", c_list)
        target_bus = b2.selectbox("Select Target Bus", ["Bus 1", "Bus 2", "Bus 3", "Bus 4"])
        
        # Calculate pending students in that class
        pending_class = st.session_state.df[(st.session_state.df['Class'] == target_class) & (st.session_state.df['Bus_Number'] == 'Unassigned')]
        
        if b3.button(f"DEPLOY {len(pending_class)} STUDENTS", type="primary", use_container_width=True):
            free_slots = BUS_CAPACITY - len(st.session_state.df[st.session_state.df['Bus_Number'] == target_bus])
            
            if len(pending_class) == 0:
                st.warning("All students of this class are already assigned.")
            elif free_slots < len(pending_class):
                st.error(f"Not enough seats in {target_bus}! Need {len(pending_class)} slots but only {free_slots} available.")
            else:
                st.session_state.df.loc[pending_class.index, 'Bus_Number'] = target_bus
                sync_all_data()
                st.success(f"SUCCESS: {len(pending_class)} students from {target_class} moved to {target_bus}!"); st.rerun()

# ==================== 7. MODULE: T-SHIRT STOCK & DASHBOARD ====================
elif menu == "👕 Inventory & Stats":
    st.title("📊 Mission Intelligence")
    
    # 👕 REAL-TIME STOCK COUNTERS
    st.subheader("👕 T-Shirt Stock Inventory")
    s_cols = st.columns(5)
    for i, sz in enumerate(["S", "M", "L", "XL", "XXL"]):
        total_stk = st.session_state.stock.get(sz, 0)
        given_stk = len(st.session_state.df[(st.session_state.df['T_Shirt_Size'] == sz) & (st.session_state.df['T_Shirt_Collected'] == 'Yes')])
        remaining = total_stk - given_stk
        
        with s_cols[i]:
            st.markdown(f"""
            <div class="stock-card">
                <div style="font-size:12px; color:#aaa;">SIZE {sz}</div>
                <div class="stock-val">{remaining}</div>
                <div style="font-size:10px; color:#888;">Remaining of {total_stk}</div>
            </div>
            """, unsafe_allow_html=True)
            if total_stk > 0:
                st.progress(max(0, min(remaining/total_stk, 1.0)))

    st.markdown("---")
    # OVERALL ANALYTICS
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Registration", len(st.session_state.df))
    m2.metric("Checked-in Done", len(st.session_state.df[st.session_state.df['Entry_Status'] == 'Done']))
    m3.metric("Kits Distributed", len(st.session_state.df[st.session_state.df['T_Shirt_Collected'] == 'Yes']))
    m4.metric("Absent Count", len(st.session_state.df[st.session_state.df['Entry_Status'] != 'Done']))

# ==================== 8. REMAINING MODULES ====================
elif menu == "➕ Manual Registration":
    st.title("➕ Manual Personnel Entry")
    with st.form("manual_reg"):
        fn = st.text_input("Full Name")
        ph = st.text_input("Contact Number")
        rl = st.selectbox("Role", ["Student", "Volunteer", "Teacher", "Staff", "Guest"])
        cs = st.text_input("Class", "N/A")
        if st.form_submit_button("ADD TO DATABASE", use_container_width=True):
            if fn and ph:
                new_data = {
                    'Name': fn, 'Role': rl, 'Spot Phone': ph, 'Guardian Phone': 'N/A',
                    'Ticket_Number': f"MAN-{int(time.time())}", 'Class': cs, 'Roll': 'N/A',
                    'Entry_Status': 'N/A', 'Entry_Time': 'N/A', 'Bus_Number': 'Unassigned',
                    'T_Shirt_Size': 'L', 'T_Shirt_Collected': 'No', 'Notes': 'Manual Admin Entry'
                }
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_data])], ignore_index=True)
                sync_all_data()
                st.success("New Entry Added Successfully!"); st.rerun()

elif menu == "📝 Master Database":
    st.title("📝 Administrative Data Access")
    st.dataframe(st.session_state.df, use_container_width=True, height=500)
    st.download_button("📥 DOWNLOAD MASTER CSV", st.session_state.df.to_csv(index=False), "event_master_data.csv")

# ==============================================================================
# FOOTER
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.caption("Willian's 26 | System V4.0 Ultra")
