import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time
import pytz
import streamlit.components.v1 as components

# ==============================================================================
# 1. ADVANCED GLOBAL CONFIGURATION & CYBER-UI DEFINITION
# ==============================================================================
st.set_page_config(
    page_title="Event OS Pro | Willian's 26 Elite", 
    page_icon="🎆", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ULTRA-DETAILED CSS ENGINE (EVERY CLASS DEFINED EXPLICITLY) ---
st.markdown("""
    <style>
    /* MAIN INTERFACE */
    .stApp {
        background-color: #000000;
        background-image: linear-gradient(rgba(0, 0, 0, 0.92), rgba(0, 0, 0, 0.95)),
            url("https://images.unsplash.com/photo-1470225620780-dba8ba36b745?q=80&w=2070&auto=format&fit=crop");
        background-size: cover; background-attachment: fixed; color: #ffffff;
    }
    
    /* SIDEBAR NAVIGATION */
    section[data-testid="stSidebar"] {
        background-color: rgba(5, 5, 5, 0.98);
        border-right: 2px solid #333;
        box-shadow: 10px 0 20px rgba(0,0,0,0.8);
    }

    /* === 🚀 ALL PREMIUM CARDS (RESTORED & UPGRADED) === */
    
    /* STUDENT: CYBER GLASS */
    .card-student {
        background: rgba(16, 30, 45, 0.7); backdrop-filter: blur(15px);
        border: 1px solid rgba(0, 255, 255, 0.3); border-radius: 20px; 
        padding: 30px; text-align: center; margin-bottom: 25px;
        transition: transform 0.3s ease;
    }
    .card-student:hover { transform: scale(1.02); }
    
    /* ORGANIZER: PURPLE PULSE */
    @keyframes pulse-purple {
        0% { box-shadow: 0 0 0 0 rgba(213, 0, 249, 0.5); }
        70% { box-shadow: 0 0 0 15px rgba(213, 0, 249, 0); }
        100% { box-shadow: 0 0 0 0 rgba(213, 0, 249, 0); }
    }
    .card-organizer {
        background: linear-gradient(135deg, rgba(40, 0, 80, 0.9), rgba(10, 0, 20, 0.95));
        border: 2px solid #d500f9; border-radius: 20px; padding: 30px; 
        text-align: center; animation: pulse-purple 2s infinite;
    }
    
    /* STAFF/TEACHER: EMERALD BORDER */
    .card-staff {
        background: linear-gradient(145deg, #002b20, #001a13);
        border-top: 4px solid #00ff88; border-bottom: 1px solid #00ff88;
        border-radius: 20px; padding: 30px; text-align: center;
    }
    
    /* ELITE/PRINCIPAL: ROYAL GOLD */
    .card-elite {
        background: linear-gradient(160deg, #111, #222); border: 2px solid #ffd700;
        box-shadow: 0 0 30px rgba(255, 215, 0, 0.4); padding: 35px; text-align: center;
        position: relative; overflow: hidden;
    }
    .card-elite::after {
        content: "VIP ACCESS"; position: absolute; top: 0; left: 50%; transform: translateX(-50%);
        background: #ffd700; color: #000; font-weight: 900; font-size: 11px;
        padding: 4px 20px; border-radius: 0 0 15px 15px;
    }

    /* CARD COMPONENTS */
    .id-name { font-size: 34px; font-weight: 900; margin: 15px 0; color: #fff; letter-spacing: 1px; }
    .info-row { display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.08); padding: 12px 0; font-size: 16px; color: #ccc; }
    .role-badge { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); padding: 6px 18px; border-radius: 30px; font-size: 12px; font-weight: bold; letter-spacing: 2px; text-transform: uppercase; }
    
    /* FORM INPUTS */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(15, 15, 15, 0.95) !important; color: #00ff88 !important; border: 1px solid #444 !important; border-radius: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. MASTER DATA ENGINE: CLOUD SYNC & RECOVERY
# ==============================================================================
conn = st.connection("gsheets", type=GSheetsConnection)
BUS_CAPACITY = 45

def get_current_time_dhaka():
    tz = pytz.timezone('Asia/Dhaka')
    return datetime.now(tz).strftime("%I:%M:%S %p")

def perform_cloud_sync(worksheet_name, dataframe):
    """Detailed sync logic with error reporting"""
    try:
        conn.update(worksheet=worksheet_name, data=dataframe)
        st.toast("✅ Cloud Synchronized Successfully", icon="🌐")
        return True
    except Exception as e:
        st.error(f"❌ DATABASE SYNC ERROR: {e}")
        return False

def load_master_records():
    """Fetches every single column from the original 463-line version"""
    try:
        df = conn.read(worksheet="Data", ttl=0)
        required_columns = [
            'Name', 'Role', 'Spot Phone', 'Guardian Phone', 'Ticket_Number', 
            'Class', 'Roll', 'Entry_Status', 'Entry_Time', 'Bus_Number', 
            'T_Shirt_Size', 'T_Shirt_Collected', 'Notes'
        ]
        for col in required_columns:
            if col not in df.columns:
                df[col] = 'N/A'
        return df.fillna("N/A").astype(str)
    except Exception as e:
        st.error(f"FATAL: Could not fetch records. {e}")
        return pd.DataFrame()

def load_inventory_stock():
    """Detailed Inventory Tracker for T-Shirt System"""
    try:
        df_stock = conn.read(worksheet="Stock", ttl=0)
        stock_map = dict(zip(df_stock['Size'], df_stock['Quantity'].astype(int)))
        return {s: int(stock_map.get(s, 0)) for s in ["S", "M", "L", "XL", "XXL"]}
    except:
        return {"S":0, "M":0, "L":0, "XL":0, "XXL":0}

# Session Management
if 'df' not in st.session_state: st.session_state.df = load_master_records()
if 'stock' not in st.session_state: st.session_state.stock = load_inventory_stock()

# ==============================================================================
# 3. AUTHENTICATION & SIDEBAR TIMER
# ==============================================================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center; color:#00ff88;'>🔒 ADMINISTRATIVE GATEWAY</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        u_login = st.text_input("Username Identity")
        p_login = st.text_input("Security PIN", type="password")
        if st.button("EXECUTE AUTHENTICATION", use_container_width=True, type="primary"):
            if u_login == "admin" and p_login == "1234":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("ACCESS DENIED: INVALID CREDENTIALS")
    st.stop()

# --- SIDEBAR: UPGRADED TIMER ---
with st.sidebar:
    st.markdown("<h2 style='color:#00ff88; margin-bottom:20px;'>⚡ MISSION CONTROL</h2>", unsafe_allow_html=True)
    
    # LIVE COUNTDOWN CALCULATOR
    target_dt = datetime(2026, 2, 3, 9, 0, 0)
    now_dt = datetime.now()
    diff = target_dt - now_dt
    
    d_left = diff.days
    h_left, rem = divmod(diff.seconds, 3600)
    m_left, s_left = divmod(rem, 60)

    timer_v3 = f"""
    <div style="background: rgba(0,255,136,0.1); border: 2px solid #00ff88; border-radius: 15px; padding: 15px; text-align: center;">
        <div style="font-size: 10px; color: #00ff88; letter-spacing: 2px;">LAUNCH SEQUENCE</div>
        <div style="display: flex; justify-content: space-around; margin-top: 10px;">
            <div><b style="font-size:20px; color:#fff;">{d_left:02d}</b><br><small style="font-size:8px;">DAYS</small></div>
            <div><b style="font-size:20px; color:#fff;">{h_left:02d}</b><br><small style="font-size:8px;">HOURS</small></div>
            <div><b style="font-size:20px; color:#fff;">{m_left:02d}</b><br><small style="font-size:8px;">MINS</small></div>
            <div><b style="font-size:20px; color:#ff4b4b;">{s_left:02d}</b><br><small style="font-size:8px;">SECS</small></div>
        </div>
    </div>
    """
    components.html(timer_v3, height=120)

    st.markdown("---")
    menu_selection = st.radio(
        "NAVIGATION INTERFACE", 
        ["🔍 Search & Records", "➕ Add New Entry", "🚌 Fleet Management", "📊 Global Analytics", "📜 View All Lists", "📝 Master Database"],
        index=0
    )
    
    if st.button("🔄 FORCE RE-SYNC"):
        st.session_state.df = load_master_records()
        st.session_state.stock = load_inventory_stock()
        st.rerun()

# ==============================================================================
# 4. MODULE: SEARCH & EXTENDED EDITOR (RESTORED EVERY SINGLE FIELD)
# ==============================================================================
if menu_selection == "🔍 Search & Records":
    st.title("🔍 Search & Management Engine")
    search_box = st.text_input("🔎 Search by Ticket ID, Full Name, or Contact Number:").strip()
    
    if search_box:
        m_df = st.session_state.df
        mask = (m_df['Name'].str.contains(search_box, case=False) | 
                m_df['Ticket_Number'].str.contains(search_box, case=False) | 
                m_df['Spot Phone'].str.contains(search_box, case=False))
        results = m_df[mask]
        
        if not results.empty:
            target_idx = results.index[0]
            row_data = m_df.loc[target_idx]
            
            # --- CARD SELECTION LOGIC (DETAILED) ---
            role_type = row_data['Role']
            if role_type in ["Principal", "College Head"]: c_type = "card-elite"
            elif role_type == "Organizer": c_type = "card-organizer"
            elif role_type in ["Teacher", "Staff"]: c_type = "card-staff"
            else: c_type = "card-student"

            col_view, col_edit = st.columns([1, 1.6])
            
            with col_view:
                st.markdown(f"""
                <div class="{c_type}">
                    <div class="role-badge">{role_type}</div>
                    <div class="id-name">{row_data['Name']}</div>
                    <div class="info-row"><span>Ticket ID</span><b style="color:#00ff88;">{row_data['Ticket_Number']}</b></div>
                    <div class="info-row"><span>Class / Roll</span><span>{row_data['Class']} / {row_data['Roll']}</span></div>
                    <div class="info-row"><span>Phone</span><span>{row_data['Spot Phone']}</span></div>
                    <div class="info-row"><span>Bus Assigned</span><span style="color:#ffd700;">{row_data['Bus_Number']}</span></div>
                    <div style="margin-top:25px; font-weight:bold; font-size:18px; color:{'#00ff88' if row_data['Entry_Status']=='Done' else '#ff4b4b'};">
                        {'✅ MISSION ENTERED' if row_data['Entry_Status']=='Done' else '⏳ PENDING ARRIVAL'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col_edit:
                with st.container(border=True):
                    st.subheader("📝 Extended Record Editor")
                    
                    # BLOCK 1: IDENTITY
                    e_name = st.text_input("Edit Full Name", row_data['Name'])
                    e_ticket = st.text_input("Update Ticket ID", row_data['Ticket_Number'])
                    
                    # BLOCK 2: CONTACTS
                    c1, c2 = st.columns(2)
                    e_phone = c1.text_input("Spot Phone", row_data['Spot Phone'])
                    e_guardian = c2.text_input("Guardian Phone", row_data['Guardian Phone'])
                    
                    # BLOCK 3: ACADEMIC & ROLE
                    c3, c4, c5 = st.columns(3)
                    role_options = ["Student", "Volunteer", "Teacher", "Staff", "Organizer", "Principal", "College Head"]
                    e_role = c3.selectbox("Role", role_options, index=role_options.index(role_type) if role_type in role_options else 0)
                    e_class = c4.text_input("Class", row_data['Class'])
                    e_roll = c5.text_input("Roll", row_data['Roll'])
                    
                    # BLOCK 4: LOGISTICS (3 NEW SYSTEMS INTEGRATED)
                    st.markdown("---")
                    c6, c7 = st.columns(2)
                    size_options = ["S", "M", "L", "XL", "XXL"]
                    e_size = c6.selectbox("T-Shirt Size", size_options, index=size_options.index(row_data['T_Shirt_Size']) if row_data['T_Shirt_Size'] in size_options else 2)
                    bus_options = ["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"]
                    e_bus = c7.selectbox("Assign Bus Fleet", bus_options, index=bus_options.index(row_data['Bus_Number']) if row_data['Bus_Number'] in bus_options else 0)
                    
                    # BLOCK 5: CHECKPOINTS
                    c8, c9 = st.columns(2)
                    e_entry = c8.toggle("Final Entry Status", row_data['Entry_Status'] == 'Done')
                    e_kit = c9.toggle("T-Shirt Kit Collected", row_data['T_Shirt_Collected'] == 'Yes')
                    e_notes = st.text_area("Administrative Notes", row_data['Notes'])

                    if st.button("💾 SAVE EXTENDED UPDATE", type="primary", use_container_width=True):
                        # Apply all updates to session dataframe
                        st.session_state.df.at[target_idx, 'Name'] = e_name
                        st.session_state.df.at[target_idx, 'Ticket_Number'] = e_ticket
                        st.session_state.df.at[target_idx, 'Spot Phone'] = e_phone
                        st.session_state.df.at[target_idx, 'Guardian Phone'] = e_guardian
                        st.session_state.df.at[target_idx, 'Role'] = e_role
                        st.session_state.df.at[target_idx, 'Class'] = e_class
                        st.session_state.df.at[target_idx, 'Roll'] = e_roll
                        st.session_state.df.at[target_idx, 'T_Shirt_Size'] = e_size
                        st.session_state.df.at[target_idx, 'Bus_Number'] = e_bus
                        st.session_state.df.at[target_idx, 'Notes'] = e_notes
                        st.session_state.df.at[target_idx, 'Entry_Status'] = "Done" if e_entry else "N/A"
                        st.session_state.df.at[target_idx, 'T_Shirt_Collected'] = "Yes" if e_kit else "No"
                        
                        if e_entry and row_data['Entry_Time'] == 'N/A':
                            st.session_state.df.at[target_idx, 'Entry_Time'] = get_current_time_dhaka()
                        
                        if perform_cloud_sync("Data", st.session_state.df):
                            st.balloons()
                            st.rerun()
        else:
            st.warning("NO MATCHING RECORDS FOUND IN DATABASE.")

# ==============================================================================
# 5. MODULE: ADVANCED BUS FLEET & BULK ASSIGN (DETAILED)
# ==============================================================================
elif menu_selection == "🚌 Fleet Management":
    st.title("🚌 Fleet & Class Operations")
    
    # --- BUS SEAT MONITOR ---
    fleet = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    f_cols = st.columns(4)
    for i, b_id in enumerate(fleet):
        b_count = len(st.session_state.df[st.session_state.df['Bus_Number'] == b_id])
        f_cols[i].metric(b_id, f"{b_count}/{BUS_CAPACITY}", f"{BUS_CAPACITY - b_count} Available")
        f_cols[i].progress(min(b_count/BUS_CAPACITY, 1.0))

    # --- 🎯 CLASS-WISE BULK ASSIGNMENT ENGINE ---
    
    st.markdown("---")
    st.subheader("🎯 Class-wise Fleet Deployment")
    with st.container(border=True):
        st.info("Select a class and assign all unassigned students from that class to a specific bus in one click.")
        all_classes = sorted([c for c in st.session_state.df['Class'].unique() if c != 'N/A'])
        
        bc1, bc2, bc3 = st.columns([2, 2, 1])
        target_c = bc1.selectbox("Filter Target Class", all_classes)
        target_b = bc2.selectbox("Select Destination Bus", fleet)
        
        # Calculate pending students for this class
        pending_in_class = st.session_state.df[(st.session_state.df['Class'] == target_c) & (st.session_state.df['Bus_Number'] == 'Unassigned')]
        
        if bc3.button(f"MOVE {len(pending_in_class)} STUDENTS", use_container_width=True, type="primary"):
            current_fill = len(st.session_state.df[st.session_state.df['Bus_Number'] == target_b])
            available_slots = BUS_CAPACITY - current_fill
            
            if len(pending_in_class) == 0:
                st.warning("Everyone in this class is already assigned.")
            elif available_slots <= 0:
                st.error(f"{target_b} is full!")
            else:
                move_count = min(len(pending_in_class), available_slots)
                indices_to_move = pending_in_class.index[:move_count]
                
                for idx in indices_to_move:
                    st.session_state.df.at[idx, 'Bus_Number'] = target_b
                
                if perform_cloud_sync("Data", st.session_state.df):
                    st.success(f"DEPLOYED {move_count} STUDENTS FROM {target_c} TO {target_b}!")
                    time.sleep(1); st.rerun()

    # --- 📄 PDF/HTML MANIFEST GENERATOR ---
    st.markdown("---")
    st.subheader("🖨️ Professional Manifest Export")
    if st.button("📄 GENERATE PRINT-READY MANIFESTS"):
        html_report = "<html><head><style>table{width:100%; border-collapse:collapse;} th,td{border:1px solid #000; padding:10px; text-align:left; font-family:sans-serif;} @media print{.pb{page-break-after:always;}}</style></head><body>"
        for b_name in fleet:
            b_df = st.session_state.df[st.session_state.df['Bus_Number'] == b_name].sort_values('Name')
            if not b_df.empty:
                html_report += f"<div class='pb'><h1>{b_name} Passenger List</h1><table><tr><th>SL</th><th>Name</th><th>Class/Roll</th><th>Phone</th><th>Signature</th></tr>"
                for i, (_, r) in enumerate(b_df.iterrows(), 1):
                    html_report += f"<tr><td>{i}</td><td>{r['Name']}</td><td>{r['Class']} / {r['Roll']}</td><td>{r['Spot Phone']}</td><td></td></tr>"
                html_report += "</table></div>"
        html_report += "</body></html>"
        st.download_button("⬇️ DOWNLOAD MANIFEST (PDF/HTML)", html_report, "Bus_Manifest.html", "text/html", use_container_width=True)

# ==============================================================================
# 6. MODULE: STRATEGIC DASHBOARD & STOCK TRACKER (DETAILED)
# ==============================================================================
elif menu_selection == "📊 Global Analytics":
    st.title("📊 Mission Intelligence")
    
    # --- 👕 T-SHIRT STOCK CHECKER ENGINE ---
    st.subheader("👕 T-Shirt Strategic Inventory")
    inv_cols = st.columns(5)
    
    # Calculate real-time consumption
    for i, size in enumerate(["S", "M", "L", "XL", "XXL"]):
        total_stk = st.session_state.stock.get(size, 0)
        delivered = len(st.session_state.df[(st.session_state.df['T_Shirt_Size'] == size) & (st.session_state.df['T_Shirt_Collected'] == 'Yes')])
        rem_stk = total_stk - delivered
        
        with inv_cols[i]:
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.05); border:1px solid {'#00ff88' if rem_stk > 5 else '#ff4b4b'}; border-radius:12px; padding:15px; text-align:center;">
                <div style="color:#aaa; font-size:12px;">SIZE {size}</div>
                <div style="font-size:28px; font-weight:900;">{rem_stk}</div>
                <div style="font-size:10px; color:#aaa;">REMAINING OF {total_stk}</div>
            </div>
            """, unsafe_allow_html=True)
            if total_stk > 0:
                st.progress(max(0, min(rem_stk/total_stk, 1.0)))
    
    # --- ATTENDANCE CHARTS ---
    st.markdown("---")
    met1, met2, met3 = st.columns(3)
    met1.metric("Total Registration", len(st.session_state.df))
    met2.metric("Check-ins Done", len(st.session_state.df[st.session_state.df['Entry_Status'] == 'Done']))
    met3.metric("Kits Distributed", len(st.session_state.df[st.session_state.df['T_Shirt_Collected'] == 'Yes']))

# ==============================================================================
# 7. REMAINING MODULES (DETAILED)
# ==============================================================================
elif menu_selection == "➕ Add New Entry":
    st.title("➕ Strategic Manual Entry")
    with st.form("manual_add_form"):
        st.info("Verified administrative access required for manual entry.")
        f_name = st.text_input("Full Legal Name")
        f_phone = st.text_input("Contact Number")
        f_role = st.selectbox("Assign Role", ["Student", "Volunteer", "Teacher", "Staff", "Guest"])
        f_cls = st.text_input("Class / Department", "N/A")
        if st.form_submit_button("➕ ADD TO CLOUD DATABASE", use_container_width=True):
            if f_name and f_phone:
                new_row = {
                    'Name': f_name, 'Role': f_role, 'Spot Phone': f_phone, 'Guardian Phone': 'N/A',
                    'Ticket_Number': f"MAN-{int(time.time())}", 'Class': f_cls, 'Roll': 'N/A',
                    'Entry_Status': 'N/A', 'Entry_Time': 'N/A', 'Bus_Number': 'Unassigned',
                    'T_Shirt_Size': 'L', 'T_Shirt_Collected': 'No', 'Notes': 'Manual Admin Entry'
                }
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
                if perform_cloud_sync("Data", st.session_state.df):
                    st.success("RECORD ADDED!"); time.sleep(1); st.rerun()

elif menu_selection == "📝 Master Database":
    st.title("📝 Database Master View")
    st.dataframe(st.session_state.df, use_container_width=True)
    st.download_button("📥 EXPORT FULL CSV", st.session_state.df.to_csv(index=False), "event_master_data.csv")

# ==============================================================================
# SYSTEM FOOTER
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.caption("Willian's 26 | System V4.0.1")
