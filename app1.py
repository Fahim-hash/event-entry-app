import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time
import pytz
import streamlit.components.v1 as components

# ==============================================================================
# 1. GLOBAL CONFIGURATION & ULTRA PREMIUM STYLING
# ==============================================================================
st.set_page_config(
    page_title="Event OS Pro | Willian's 26 | Management Suite", 
    page_icon="🎆", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DETAILED CSS (EVERY STYLE DEFINED EXPLICITLY) ---
st.markdown("""
    <style>
    /* 🔥 MAIN APP BACKGROUND 🔥 */
    .stApp {
        background-color: #000000;
        background-image: 
            linear-gradient(rgba(0, 0, 0, 0.92), rgba(0, 0, 0, 0.96)),
            url("https://images.unsplash.com/photo-1470225620780-dba8ba36b745?q=80&w=2070&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
        color: #ffffff;
    }
    
    /* SIDEBAR STYLING */
    section[data-testid="stSidebar"] {
        background-color: rgba(5, 5, 5, 0.98);
        border-right: 1px solid #333;
        box-shadow: 5px 0 15px rgba(0,0,0,0.5);
    }

    /* === 🚀 ALL DETAILED CARD CLASSES === */
    
    /* CARD 1: STUDENT (CYBER BLUE) */
    .card-student {
        background: rgba(16, 30, 45, 0.7);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(0, 255, 255, 0.3);
        box-shadow: 0 8px 32px 0 rgba(0, 255, 255, 0.1);
        border-radius: 20px; 
        padding: 25px; 
        text-align: center; 
        margin-bottom: 25px;
        transition: transform 0.4s ease, box-shadow 0.4s ease;
    }
    .card-student:hover { transform: translateY(-8px); box-shadow: 0 12px 40px rgba(0, 255, 255, 0.2); }

    /* CARD 2: ORGANIZER (NEON PURPLE) */
    @keyframes pulse-purple-glow {
        0% { box-shadow: 0 0 5px rgba(213, 0, 249, 0.4); }
        50% { box-shadow: 0 0 25px rgba(213, 0, 249, 0.7); }
        100% { box-shadow: 0 0 5px rgba(213, 0, 249, 0.4); }
    }
    .card-organizer {
        background: linear-gradient(135deg, rgba(40, 0, 80, 0.8), rgba(10, 0, 20, 0.9));
        border: 2px solid #d500f9;
        border-radius: 20px; 
        padding: 25px; 
        text-align: center; 
        margin-bottom: 25px;
        animation: pulse-purple-glow 3s infinite;
    }

    /* CARD 3: STAFF/TEACHER (EMERALD) */
    .card-staff {
        background: linear-gradient(145deg, #002b20, #001a13);
        border-left: 5px solid #00ff88;
        border-right: 1px solid #00ff88;
        border-radius: 20px; 
        padding: 25px; 
        text-align: center; 
        margin-bottom: 25px;
        box-shadow: 0 10px 20px rgba(0, 255, 136, 0.1);
    }

    /* CARD 4: ELITE ROYAL (GOLD) */
    .card-elite {
        background: linear-gradient(160deg, #111 0%, #222 100%);
        border: 2px solid #ffd700;
        box-shadow: 0 0 30px rgba(255, 215, 0, 0.3);
        padding: 30px; 
        text-align: center; 
        margin-bottom: 25px;
        position: relative;
        overflow: hidden;
    }
    .card-elite::before {
        content: ""; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
        background: radial-gradient(circle, rgba(255,215,0,0.1) 0%, transparent 70%);
    }
    .card-elite::after {
        content: "⭐ VIP ACCESS ⭐";
        position: absolute; top: 0; left: 50%; transform: translateX(-50%);
        background: #ffd700; color: #000; font-weight: 900; font-size: 10px;
        padding: 3px 15px; border-radius: 0 0 10px 10px;
    }

    /* TEXT COMPONENTS */
    .id-name { font-size: 32px; font-weight: 800; margin: 15px 0; color: #fff; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }
    .role-badge { 
        display: inline-block; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2);
        padding: 5px 20px; border-radius: 50px; font-size: 12px; font-weight: bold; letter-spacing: 1.5px; text-transform: uppercase;
    }
    .info-row { 
        display: flex; justify-content: space-between; align-items: center;
        padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.08); font-size: 15px; color: #ddd;
    }
    
    /* INPUT BOX DECORATION */
    .stTextInput input { border-radius: 10px !important; border: 1px solid #444 !important; background: #111 !important; color: #00ff88 !important; }
    .stSelectbox div[data-baseweb="select"] { border-radius: 10px !important; background: #111 !important; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. DATA ENGINE: MASTER FUNCTIONS
# ==============================================================================
conn = st.connection("gsheets", type=GSheetsConnection)
BUS_CAPACITY = 45

def get_current_dhaka_time():
    tz = pytz.timezone('Asia/Dhaka')
    return datetime.now(tz).strftime("%H:%M:%S")

def sync_to_cloud(worksheet_name, dataframe):
    """Detailed sync function with error reporting"""
    try:
        conn.update(worksheet=worksheet_name, data=dataframe)
        return True
    except Exception as e:
        st.error(f"FATAL ERROR DURING SYNC: {str(e)}")
        return False

def fetch_master_data():
    """Load and repair dataframe columns"""
    try:
        df = conn.read(worksheet="Data", ttl=0)
        expected = [
            'Name', 'Role', 'Spot Phone', 'Guardian Phone', 'Ticket_Number', 
            'Class', 'Roll', 'Entry_Status', 'Entry_Time', 'Bus_Number', 
            'T_Shirt_Size', 'T_Shirt_Collected', 'Notes'
        ]
        for col in expected:
            if col not in df.columns:
                df[col] = 'N/A'
        return df.fillna("N/A").astype(str)
    except Exception as e:
        st.error(f"Data Fetch Failure: {e}")
        return pd.DataFrame()

def fetch_stock_levels():
    """Retrieve detailed inventory from Stock sheet"""
    try:
        df_s = conn.read(worksheet="Stock", ttl=0)
        inventory = dict(zip(df_s['Size'], df_s['Quantity']))
        return {s: int(float(inventory.get(s, 0))) for s in ["S", "M", "L", "XL", "XXL"]}
    except:
        return {"S":0, "M":0, "L":0, "XL":0, "XXL":0}

# Initialize Sessions
if 'df' not in st.session_state: st.session_state.df = fetch_master_data()
if 'stock' not in st.session_state: st.session_state.stock = fetch_stock_levels()

# ==============================================================================
# 3. AUTHENTICATION SYSTEM
# ==============================================================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center;'>🔐 SECURE GATEWAY</h1>", unsafe_allow_html=True)
    with st.container():
        _, center, _ = st.columns([1,2,1])
        with center:
            u_input = st.text_input("Administrator Identity")
            p_input = st.text_input("Access Key", type="password")
            if st.button("AUTHENTICATE", use_container_width=True, type="primary"):
                if u_input == "admin" and p_input == "1234":
                    st.session_state.logged_in = True
                    st.toast("Access Granted", icon="✅")
                    st.rerun()
                else:
                    st.error("Access Denied: Invalid Credentials")
    st.stop()

# ==============================================================================
# 4. SIDEBAR & NAVIGATION
# ==============================================================================
with st.sidebar:
    st.markdown("<h2 style='color:#00ff88;'>⚡ CONTROL CENTER</h2>", unsafe_allow_html=True)
    
    # COUNTDOWN COMPONENT
    timer_code = """
    <div style="background: rgba(0,255,136,0.1); border: 1px solid #00ff88; padding: 15px; border-radius: 15px; text-align: center;">
        <div style="color: #00ff88; font-size: 10px; letter-spacing: 2px;">EVENT GO-LIVE</div>
        <div style="font-size: 22px; font-weight: 800; color: #fff; margin: 5px 0;">3 FEB 2026</div>
        <div style="color: #aaa; font-size: 10px;">DHAKA, BANGLADESH</div>
    </div>
    """
    components.html(timer_code, height=110)
    
    st.markdown("---")
    nav_choice = st.radio(
        "SELECT MODULE", 
        ["🔍 Search & Entry", "➕ Add New Entry", "📜 View Full Lists", "🚫 Absentee Manager", "🚌 Fleet & Class Manager", "📊 Dashboard", "📝 Database Master"],
        index=0
    )
    
    if st.button("🔄 FORCE REFRESH CLOUD"):
        st.cache_data.clear()
        st.session_state.df = fetch_master_data()
        st.session_state.stock = fetch_stock_levels()
        st.rerun()

# ==============================================================================
# 5. MODULE: SEARCH & DETAILED ENTRY
# ==============================================================================
if nav_choice == "🔍 Search & Entry":
    st.title("🔍 Search & Entry Module")
    search_query = st.text_input("🔎 Search by Ticket ID, Full Name, or Phone Number:").strip()
    
    if search_query:
        master_df = st.session_state.df
        match_mask = (
            master_df['Name'].str.contains(search_query, case=False) | 
            master_df['Ticket_Number'].str.contains(search_query, case=False) | 
            master_df['Spot Phone'].str.contains(search_query, case=False)
        )
        results = master_df[match_mask]
        
        if not results.empty:
            target_idx = results.index[0]
            p_data = master_df.loc[target_idx]
            
            # --- DETAILED CARD LOGIC ---
            role_type = p_data['Role']
            if role_type in ["Principal", "College Head"]: css_card = "card-elite"
            elif role_type == "Organizer": css_card = "card-organizer"
            elif role_type in ["Teacher", "Staff", "College Staff"]: css_card = "card-staff"
            else: css_card = "card-student"

            # LAYOUT: CARD | EDITOR
            view_col, edit_col = st.columns([1, 1.6])
            
            with view_col:
                is_checked = p_data['Entry_Status'] == 'Done'
                st.markdown(f"""
                <div class="{css_card}">
                    <div class="role-badge">{role_type}</div>
                    <div class="id-name">{p_data['Name']}</div>
                    <div class="info-row"><span>Ticket No</span><span style="color:#00ff88; font-weight:bold;">{p_data['Ticket_Number']}</span></div>
                    <div class="info-row"><span>Class / Roll</span><span>{p_data['Class']} / {p_data['Roll']}</span></div>
                    <div class="info-row"><span>Bus Assigned</span><span>{p_data['Bus_Number']}</span></div>
                    <div class="info-row"><span>T-Shirt Size</span><span>{p_data['T_Shirt_Size']}</span></div>
                    <div style="margin-top:20px; font-size:20px; font-weight:bold; color:{'#00ff88' if is_checked else '#ff4b4b'};">
                        {'✅ STATUS: ENTERED' if is_checked else '⏳ STATUS: PENDING'}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # QUICK ACTIONS
                st.subheader("⚡ Quick Actions")
                if not is_checked:
                    if st.button("🚀 INSTANT CHECK-IN", type="primary", use_container_width=True):
                        st.session_state.df.at[target_idx, 'Entry_Status'] = 'Done'
                        st.session_state.df.at[target_idx, 'Entry_Time'] = get_current_dhaka_time()
                        if sync_to_cloud("Data", st.session_state.df):
                            st.success(f"{p_data['Name']} Entered!"); time.sleep(0.5); st.rerun()

            with edit_col:
                with st.container(border=True):
                    st.subheader("✏️ Master Editor")
                    
                    # BLOCK 1: PERSONAL
                    ed_name = st.text_input("Edit Full Name", p_data['Name'])
                    c1, c2 = st.columns(2)
                    ed_phone = c1.text_input("Spot Phone", p_data['Spot Phone'])
                    ed_guardian = c2.text_input("Guardian Phone", p_data['Guardian Phone'])
                    
                    # BLOCK 2: ROLE & ACADEMIC
                    c3, c4, c5 = st.columns(3)
                    role_list = ["Student", "Volunteer", "Teacher", "Staff", "Organizer", "Principal"]
                    ed_role = c3.selectbox("Assign Role", role_list, index=role_list.index(role_type) if role_type in role_list else 0)
                    ed_class = c4.text_input("Class", p_data['Class'])
                    ed_roll = c5.text_input("Roll", p_data['Roll'])
                    
                    # BLOCK 3: LOGISTICS
                    st.markdown("---")
                    c6, c7 = st.columns(2)
                    size_list = ["S", "M", "L", "XL", "XXL"]
                    ed_size = c6.selectbox("T-Shirt Size", size_list, index=size_list.index(p_data['T_Shirt_Size']) if p_data['T_Shirt_Size'] in size_list else 2)
                    bus_list = ["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"]
                    ed_bus = c7.selectbox("Assign Bus", bus_list, index=bus_list.index(p_data['Bus_Number']) if p_data['Bus_Number'] in bus_list else 0)
                    
                    # BLOCK 4: TOGGLES
                    c8, c9 = st.columns(2)
                    ed_ent = c8.toggle("Entry Done", p_data['Entry_Status'] == 'Done')
                    ed_kit = c9.toggle("T-Shirt Collected", p_data['T_Shirt_Collected'] == 'Yes')
                    
                    if st.button("💾 SAVE MASTER DATA", use_container_width=True, type="primary"):
                        # Logic for Stock Management
                        old_kit = p_data['T_Shirt_Collected'] == 'Yes'
                        old_size = p_data['T_Shirt_Size']
                        
                        # Apply Updates
                        st.session_state.df.at[target_idx, 'Name'] = ed_name
                        st.session_state.df.at[target_idx, 'Spot Phone'] = ed_phone
                        st.session_state.df.at[target_idx, 'Guardian Phone'] = ed_guardian
                        st.session_state.df.at[target_idx, 'Role'] = ed_role
                        st.session_state.df.at[target_idx, 'Class'] = ed_class
                        st.session_state.df.at[target_idx, 'Roll'] = ed_roll
                        st.session_state.df.at[target_idx, 'T_Shirt_Size'] = ed_size
                        st.session_state.df.at[target_idx, 'Bus_Number'] = ed_bus
                        st.session_state.df.at[target_idx, 'Entry_Status'] = 'Done' if ed_ent else 'N/A'
                        st.session_state.df.at[target_idx, 'T_Shirt_Collected'] = 'Yes' if ed_kit else 'No'
                        
                        if ed_ent and p_data['Entry_Time'] == 'N/A':
                            st.session_state.df.at[target_idx, 'Entry_Time'] = get_current_dhaka_time()
                        
                        if sync_to_cloud("Data", st.session_state.df):
                            st.success("DATABASE UPDATED!"); time.sleep(0.5); st.rerun()
        else:
            st.warning("No record found matching your query.")

# ==============================================================================
# 6. MODULE: BUS FLEET & CLASS MANAGER (DETAILED)
# ==============================================================================
elif nav_choice == "🚌 Fleet & Class Manager":
    st.title("🚌 Advanced Fleet Management")
    
    buses = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    
    # --- VISUAL LOAD MONITOR ---
    st.subheader("📊 Real-time Bus Occupancy")
    monitor_cols = st.columns(4)
    for i, b_name in enumerate(buses):
        b_filter = st.session_state.df[st.session_state.df['Bus_Number'] == b_name]
        b_count = len(b_filter)
        percent = min(b_count / BUS_CAPACITY, 1.0)
        
        with monitor_cols[i]:
            st.metric(b_name, f"{b_count}/{BUS_CAPACITY}", f"{BUS_CAPACITY - b_count} Available")
            st.progress(percent)
            if b_count >= BUS_CAPACITY:
                st.error("FULL")
            elif b_count >= 40:
                st.warning("ALMOST FULL")
            else:
                st.success("SPACE AVAILABLE")

    # --- 🎯 CLASS-WISE BULK ASSIGNMENT SYSTEM ---
    st.markdown("---")
    st.subheader("🎯 Class-wise Bulk Assignment")
    st.info("Select a class and assign all unassigned students to a specific bus.")
    
    c_list = sorted([c for c in st.session_state.df['Class'].unique() if c != 'N/A'])
    
    col_a, col_b, col_c = st.columns(3)
    target_class = col_a.selectbox("Choose Target Class", c_list)
    target_bus_name = col_b.selectbox("Select Target Bus", buses)
    
    # Calculate potential moves
    unassigned_in_class = st.session_state.df[(st.session_state.df['Class'] == target_class) & (st.session_state.df['Bus_Number'] == 'Unassigned')]
    can_move = len(unassigned_in_class)
    
    if col_c.button(f"MOVE {can_move} STUDENTS", use_container_width=True):
        current_bus_fill = len(st.session_state.df[st.session_state.df['Bus_Number'] == target_bus_name])
        available_seats = BUS_CAPACITY - current_bus_fill
        
        if can_move == 0:
            st.warning("All students in this class are already assigned.")
        elif available_seats <= 0:
            st.error("Target bus has no seats left!")
        else:
            to_move = min(can_move, available_seats)
            indices_to_update = unassigned_in_class.index[:to_move]
            
            for idx in indices_to_update:
                st.session_state.df.at[idx, 'Bus_Number'] = target_bus_name
            
            if sync_to_cloud("Data", st.session_state.df):
                st.success(f"Moved {to_move} students from {target_class} to {target_bus_name}")
                st.rerun()

    # --- 🖨️ PRINT-READY MANIFEST SYSTEM ---
    st.markdown("---")
    st.subheader("🖨️ Generate Professional Bus Manifest")
    if st.button("📄 Prepare Manifest for Printing (A4 Format)"):
        html_doc = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                .page { page-break-after: always; border: 2px solid #333; padding: 20px; margin-bottom: 20px; }
                h1 { text-align: center; color: #000; text-decoration: underline; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid #000; padding: 10px; text-align: left; font-size: 12px; }
                th { background-color: #f2f2f2; }
                .footer { margin-top: 30px; font-size: 10px; text-align: right; }
            </style>
        </head>
        <body>
        """
        for b_name in buses:
            passengers = st.session_state.df[st.session_state.df['Bus_Number'] == b_name].sort_values(by='Name')
            if not passengers.empty:
                html_doc += f"<div class='page'><h1>{b_name} Manifest</h1>"
                html_doc += f"<p>Total Passengers: {len(passengers)} | Capacity: {BUS_CAPACITY}</p>"
                html_doc += "<table><thead><tr><th>SL</th><th>Passenger Name</th><th>Class/Roll</th><th>Phone</th><th>Signature</th></tr></thead><tbody>"
                for i, (_, p_row) in enumerate(passengers.iterrows(), 1):
                    html_doc += f"<tr><td>{i}</td><td>{p_row['Name']}</td><td>{p_row['Class']} / {p_row['Roll']}</td><td>{p_row['Spot Phone']}</td><td></td></tr>"
                html_doc += "</tbody></table><div class='footer'>Generated by Event OS Pro - Willian's 26</div></div>"
        
        html_doc += "</body></html>"
        st.download_button("⬇️ DOWNLOAD PRINT-READY MANIFEST", html_doc, "Bus_Manifest_Pro.html", "text/html", use_container_width=True)

# ==============================================================================
# 7. MODULE: DASHBOARD & STOCK TRACKER (DETAILED)
# ==============================================================================
elif nav_choice == "📊 Dashboard":
    st.title("📊 Strategic Dashboard")
    
    # --- 👕 DETAILED REMAINING STOCK CALCULATION ---
    st.subheader("👕 T-Shirt Inventory Analysis (Actual vs Remaining)")
    
    # Calculate current usage
    stock_df = pd.DataFrame(list(st.session_state.stock.items()), columns=['Size', 'Total_Ordered'])
    
    dist_counts = st.session_state.df[st.session_state.df['T_Shirt_Collected'] == 'Yes']['T_Shirt_Size'].value_counts()
    
    stock_df['Distributed'] = stock_df['Size'].apply(lambda x: dist_counts.get(x, 0))
    stock_df['Remaining'] = stock_df['Total_Ordered'] - stock_df['Distributed']
    
    # Visual Cards for Stock
    stock_cols = st.columns(5)
    for i, row_s in stock_df.iterrows():
        with stock_cols[i]:
            st.metric(f"Size {row_s['Size']}", f"{row_s['Remaining']} Left", f"Total: {row_s['Total_Ordered']}")
            progress_val = max(0, min(row_s['Remaining'] / row_s['Total_Ordered'], 1.0)) if row_s['Total_Ordered'] > 0 else 0
            st.progress(progress_val)
            if row_s['Remaining'] <= 5: st.warning("Critically Low")

    # --- 📈 ATTENDANCE & DEMOGRAPHICS ---
    st.markdown("---")
    st.subheader("📈 Attendance & Demographics")
    
    met1, met2, met3, met4 = st.columns(4)
    total_reg = len(st.session_state.df)
    total_in = len(st.session_state.df[st.session_state.df['Entry_Status'] == 'Done'])
    
    met1.metric("Total Registered", total_reg)
    met2.metric("Total Checked-in", total_in, f"{round((total_in/total_reg)*100,1)}%")
    met3.metric("Pending Arrivals", total_reg - total_in)
    met4.metric("Kits Distributed", stock_df['Distributed'].sum())

    st.markdown("---")
    # Graphs
    gc1, gc2 = st.columns(2)
    with gc1:
        st.markdown("#### Role Distribution")
        st.bar_chart(st.session_state.df['Role'].value_counts())
    with gc2:
        st.markdown("#### T-Shirt Size Preference")
        st.bar_chart(st.session_state.df['T_Shirt_Size'].value_counts())

# ==============================================================================
# 8. REMAINING MODULES (DETAILED)
# ==============================================================================
elif nav_choice == "➕ Add New Entry":
    st.title("➕ Strategic Manual Entry")
    with st.form("detailed_add_form"):
        st.info("Ensure all information is verified before adding to the cloud database.")
        f_name = st.text_input("Full Name")
        f_role = st.selectbox("Assign Role", ["Student", "Volunteer", "Teacher", "Staff", "Guest"])
        f_phone = st.text_input("Phone Number")
        f_class = st.text_input("Class / Dept", "N/A")
        f_size = st.selectbox("T-Shirt Size", ["S", "M", "L", "XL", "XXL"], index=2)
        
        if st.form_submit_button("➕ ADD TO DATABASE"):
            if not f_name or not f_phone:
                st.error("Name and Phone are mandatory fields.")
            else:
                new_entry = {
                    'Name': f_name, 'Role': f_role, 'Spot Phone': f_phone, 'Guardian Phone': 'N/A',
                    'Ticket_Number': f"MAN-{int(time.time())}", 'Class': f_class, 'Roll': 'N/A',
                    'Entry_Status': 'N/A', 'Entry_Time': 'N/A', 'Bus_Number': 'Unassigned',
                    'T_Shirt_Size': f_size, 'T_Shirt_Collected': 'No', 'Notes': 'Manual Entry'
                }
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_entry])], ignore_index=True)
                if sync_to_cloud("Data", st.session_state.df):
                    st.success("New Entry Added to Cloud!"); time.sleep(1); st.rerun()

elif nav_choice == "🚫 Absentee Manager":
    st.title("🚫 Absentee List")
    absent_df = st.session_state.df[st.session_state.df['Entry_Status'] != 'Done']
    st.metric("Total Absent Students", len(absent_df))
    st.dataframe(absent_df[['Name', 'Class', 'Role', 'Spot Phone', 'Guardian Phone']], use_container_width=True)

elif nav_choice == "📝 Database Master":
    st.title("📝 Master Database Control")
    st.warning("Directly viewing the master database. Changes here should be made through edit modules.")
    st.dataframe(st.session_state.df, use_container_width=True)
    st.download_button("📥 Export Full Database (CSV)", st.session_state.df.to_csv(index=False), "master_event_data.csv", "text/csv")

# ==============================================================================
# FOOTER
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.caption("System Built by Gemini AI | Visuals by CineMotion")
