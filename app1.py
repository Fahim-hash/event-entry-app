import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time
import altair as alt  # For Charts

# ==============================================================================
# 0. SYSTEM CONFIGURATION & ASSETS
# ==============================================================================
st.set_page_config(
    page_title="Event OS Ultimate",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🎨 ULTRA PREMIUM CSS STYLING ---
st.markdown("""
    <style>
    /* 🌌 GLOBAL THEME */
    .stApp {
        background-color: #050505;
        background-image: radial-gradient(circle at 50% 50%, #1a1a1a 0%, #000000 100%);
        color: #e0e0e0;
    }
    
    /* 📦 METRIC CARDS (NEON GLOW) */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border: 1px solid rgba(0, 255, 255, 0.3);
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.2);
    }
    
    /* 🆔 DIGITAL ID CARD (HOLOGRAPHIC STYLE) */
    .id-card-container {
        perspective: 1000px;
        margin-bottom: 20px;
    }
    .id-card {
        background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
        border: 2px solid #333;
        border-radius: 20px;
        padding: 0;
        color: #fff;
        text-align: center;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        overflow: hidden;
        position: relative;
    }
    .id-header {
        background: linear-gradient(90deg, #00c6ff, #0072ff);
        padding: 15px;
        font-size: 18px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .id-body {
        padding: 25px;
    }
    .id-role-badge {
        background: #ff9966;  /* fallback for old browsers */
        background: -webkit-linear-gradient(to right, #ff5e62, #ff9966);  /* Chrome 10-25, Safari 5.1-6 */
        background: linear-gradient(to right, #ff5e62, #ff9966); /* W3C, IE 10+/ Edge, Firefox 16+, Chrome 26+, Opera 12+, Safari 7+ */
        color: white;
        padding: 5px 20px;
        border-radius: 50px;
        font-size: 12px;
        font-weight: 800;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 10px;
        box-shadow: 0 5px 15px rgba(255, 94, 98, 0.4);
    }
    .id-name {
        font-size: 32px;
        font-weight: 800;
        margin: 10px 0;
        background: -webkit-linear-gradient(#fff, #aaa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .id-detail-row {
        display: flex;
        justify-content: space-between;
        margin: 8px 0;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        padding-bottom: 5px;
        font-size: 14px;
        color: #ccc;
    }
    .id-qr {
        margin-top: 20px;
        padding: 10px;
        background: white;
        display: inline-block;
        border-radius: 10px;
    }
    .status-verified {
        color: #00ff88;
        font-weight: bold;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    }
    .status-pending {
        color: #ffcc00;
        font-weight: bold;
    }
    
    /* 🔘 CUSTOM BUTTONS */
    .stButton > button {
        border-radius: 10px;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.02);
    }
    
    /* 📊 CHARTS CONTAINER */
    .chart-container {
        background: #111;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #333;
    }
    
    /* 🏷️ INPUT FIELDS */
    input[type="text"], input[type="password"] {
        background-color: #1a1a1a !important;
        color: white !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 1. AUTHENTICATION & SESSION MANAGEMENT
# ==============================================================================
USERS = {
    "admin": {"password": "1234", "role": "admin", "name": "System Administrator"},
    "gate": {"password": "entry26", "role": "volunteer", "name": "Gate Officer"},
    "food": {"password": "food26", "role": "volunteer", "name": "Food Manager"}
}

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.logs = [] # Audit Logs

def add_log(action):
    """Adds an action to the audit log with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    user = st.session_state.get('user_name', 'Unknown')
    st.session_state.logs.insert(0, f"[{timestamp}] {user}: {action}")

def check_login():
    user = st.session_state['username']
    pwd = st.session_state['password']
    if user in USERS and USERS[user]["password"] == pwd:
        st.session_state.logged_in = True
        st.session_state.user_role = USERS[user]["role"]
        st.session_state.user_name = USERS[user]["name"]
        st.toast(f"Welcome back, {USERS[user]['name']}!", icon="👋")
        st.rerun()
    else:
        st.error("❌ Access Denied: Invalid Credentials")

if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.title("⚡ Event OS")
        st.caption("Secure Access Terminal")
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Authenticate", on_click=check_login, type="primary", use_container_width=True)
    st.stop()

# ==============================================================================
# 2. DATA LAYER (GOOGLE SHEETS)
# ==============================================================================
BUS_CAPACITY = 45
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def fetch_data():
    try:
        df = conn.read(worksheet="Data", ttl=0)
        # Define Schema
        cols = [
            'Name', 'Role', 'Spot Phone', 'Guardian Phone', 'Ticket_Number', 
            'Class', 'Roll', 'Entry_Status', 'Entry_Time', 
            'Bus_Number', 'T_Shirt_Size', 'T_Shirt_Collected', 
            'Food_Collected', 'Notes'
        ]
        # Ensure Schema
        for c in cols:
            if c not in df.columns: df[c] = ''
            
        # Clean Data Types (Crucial for Search)
        text_cols = ['Ticket_Number', 'Spot Phone', 'Guardian Phone', 'Roll', 'Class', 'Name']
        for col in text_cols:
            df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().replace('nan', 'N/A')
            
        df = df.fillna('')
        return df
    except Exception as e:
        st.error(f"Database Connection Failed: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def fetch_stock():
    try:
        df_s = conn.read(worksheet="Stock", ttl=0)
        stock = dict(zip(df_s['Size'], df_s['Quantity']))
        for s in ["S", "M", "L", "XL", "XXL"]: 
            if s not in stock: stock[s] = 0
        return stock
    except: return {"S":0, "M":0, "L":0, "XL":0, "XXL":0}

# Initialize Data
if 'df' not in st.session_state:
    st.session_state.df = fetch_data()
if 'stock' not in st.session_state:
    st.session_state.stock = fetch_stock()

def save_db():
    try:
        conn.update(worksheet="Data", data=st.session_state.df)
        add_log("Database synchronized with Cloud.")
    except Exception as e:
        st.error(f"Save Failed: {e}")

def save_inv():
    try:
        data = [{"Size": k, "Quantity": v} for k, v in st.session_state.stock.items()]
        conn.update(worksheet="Stock", data=pd.DataFrame(data))
    except: st.error("Stock Update Failed")

# ==============================================================================
# 3. SIDEBAR & NAVIGATION
# ==============================================================================
with st.sidebar:
    st.title("⚡ Event OS")
    st.write(f"Logged in as: **{st.session_state.user_name}**")
    st.markdown("---")
    
    menu = st.radio("Navigation", [
        "🏠 Dashboard", 
        "🔍 Search & Entry", 
        "👨‍🏫 Teachers", 
        "🚌 Smart Transport", 
        "📦 Inventory (Kit/Food)", 
        "📊 Analytics", 
        "⚙️ Admin & Logs"
    ])
    
    st.markdown("---")
    
    # Quick Actions
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Sync"):
            st.cache_data.clear()
            st.session_state.df = fetch_data()
            st.session_state.stock = fetch_stock()
            st.toast("System Synced!", icon="♻️")
            st.rerun()
    with c2:
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # Admin Fast Add
    if st.session_state.user_role == 'admin':
        with st.expander("⚡ Fast Add User"):
            with st.form("fast_add"):
                n = st.text_input("Name")
                r = st.selectbox("Role", ["Student", "Volunteer", "Teacher", "Guest"])
                t = st.text_input("Ticket")
                p = st.text_input("Phone")
                if st.form_submit_button("Create"):
                    if n and t and p:
                        new_row = {
                            'Name': n, 'Role': r, 'Ticket_Number': str(t), 'Spot Phone': str(p),
                            'Class': 'New', 'Roll': 'N/A', 'Entry_Status': '', 
                            'Bus_Number': 'Unassigned', 'T_Shirt_Size': 'L', 
                            'T_Shirt_Collected': 'No', 'Food_Collected': 'No'
                        }
                        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
                        save_db()
                        st.success("User Created!")
                        st.rerun()
                    else: st.warning("Fields missing")

# ==============================================================================
# 4. MODULE: DASHBOARD
# ==============================================================================
if menu == "🏠 Dashboard":
    st.title("🚀 Command Center")
    df = st.session_state.df
    
    # 4.1 Live Metrics
    tot = len(df)
    ent = len(df[df['Entry_Status']=='Done'])
    kit = len(df[df['T_Shirt_Collected']=='Yes'])
    food = len(df[df['Food_Collected']=='Yes'])
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Pax", tot, delta="Registered")
    c2.metric("Checked In", ent, delta=f"{round(ent/tot*100,1)}%" if tot else "0%", delta_color="inverse")
    c3.metric("Kits Distributed", kit, delta="Merch")
    c4.metric("Meals Served", food, delta="Lunch/Snack")
    
    st.progress(ent/tot if tot else 0)
    
    # 4.2 Charts (Time Series)
    st.markdown("### 📈 Live Traffic")
    if ent > 0:
        # Create Data for Chart
        chart_data = df[df['Entry_Status']=='Done'].copy()
        chart_data['Time'] = pd.to_datetime(chart_data['Entry_Time'], format='%H:%M:%S', errors='coerce').dt.hour
        hourly_counts = chart_data['Time'].value_counts().reset_index()
        hourly_counts.columns = ['Hour', 'Count']
        
        c = alt.Chart(hourly_counts).mark_area(
            line={'color':'cyan'},
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color='cyan', offset=0),
                       alt.GradientStop(color='rgba(0,0,0,0)', offset=1)],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(
            x=alt.X('Hour:O', title='Hour of Day'),
            y=alt.Y('Count:Q', title='Entries'),
            tooltip=['Hour', 'Count']
        ).properties(height=300)
        st.altair_chart(c, use_container_width=True)
    else:
        st.info("No entry data available for charts yet.")

    # 4.3 Activity Stream
    st.markdown("### 📡 Live Feed")
    recent = df[df['Entry_Status']=='Done'].sort_values('Entry_Time', ascending=False).head(5)
    for index, row in recent.iterrows():
        st.success(f"✅ **{row['Name']}** ({row['Role']}) entered at **{row['Entry_Time']}**")

# ==============================================================================
# 5. MODULE: SEARCH & TERMINAL (DIGITAL ID)
# ==============================================================================
elif menu == "🔍 Search & Entry":
    st.title("🔍 Access Terminal")
    
    # 5.1 Universal Search
    search_term = st.text_input("🔎 Scan Ticket / Enter Name / Phone:", placeholder="Type to search...").strip()
    
    if search_term:
        mask = (
            st.session_state.df['Name'].astype(str).str.contains(search_term, case=False) |
            st.session_state.df['Ticket_Number'].astype(str).str.contains(search_term, case=False) |
            st.session_state.df['Spot Phone'].astype(str).str.contains(search_term, case=False) |
            st.session_state.df['Guardian Phone'].astype(str).str.contains(search_term, case=False)
        )
        results = st.session_state.df[mask]
        
        if not results.empty:
            if len(results) > 1:
                st.warning(f"Found {len(results)} matches. Select specific user:")
                selected_name = st.selectbox("Select User", results['Name'].unique())
                row_idx = results[results['Name'] == selected_name].index[0]
            else:
                row_idx = results.index[0]
            
            row = st.session_state.df.loc[row_idx]
            
            # 5.2 Digital ID Interface
            col_id, col_ops = st.columns([1, 1.5])
            
            with col_id:
                # QR Code Generation URL
                qr_data = f"TICKET:{row['Ticket_Number']}|NAME:{row['Name']}"
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={qr_data}"
                
                # Dynamic Status Colors
                status_color = "#00ff88" if row['Entry_Status'] == 'Done' else "#ff4444"
                status_text = "VERIFIED ENTRY" if row['Entry_Status'] == 'Done' else "NOT CHECKED IN"
                
                # HTML ID Card
                st.markdown(f"""
                <div class="id-card-container">
                    <div class="id-card">
                        <div class="id-header">Official Event Pass</div>
                        <div class="id-body">
                            <div class="id-role-badge">{row['Role']}</div>
                            <div class="id-name">{row['Name']}</div>
                            
                            <div class="id-detail-row"><span>Ticket ID</span><span>{row['Ticket_Number']}</span></div>
                            <div class="id-detail-row"><span>Class/Roll</span><span>{row['Class']} / {row['Roll']}</span></div>
                            <div class="id-detail-row"><span>Phone</span><span>{row['Spot Phone']}</span></div>
                            <div class="id-detail-row"><span>Guardian</span><span>{row['Guardian Phone']}</span></div>
                            <div class="id-detail-row"><span>Transport</span><span>{row['Bus_Number']}</span></div>
                            
                            <div style="background: white; padding: 10px; margin-top: 15px; border-radius: 10px; display: inline-block;">
                                <img src="{qr_url}" width="120" />
                            </div>
                            
                            <div style="margin-top: 15px; color: {status_color}; font-weight: bold; border: 1px solid {status_color}; padding: 5px; border-radius: 5px;">
                                {status_text}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Printable Link
                st.download_button("🖨️ Download/Print Badge", data=f"Badge for {row['Name']}", file_name=f"Badge_{row['Ticket_Number']}.txt")

            # 5.3 Operations Panel
            with col_ops:
                st.markdown("### ⚡ Quick Operations")
                
                with st.container(border=True):
                    c1, c2, c3 = st.columns(3)
                    
                    # Entry Toggle
                    is_entered = c1.toggle("✅ Check In", value=(row['Entry_Status']=='Done'))
                    
                    # Kit Toggle
                    sz = row['T_Shirt_Size']
                    rem = st.session_state.stock.get(sz, 0)
                    is_kit = c2.toggle(f"👕 Kit ({sz})", value=(row['T_Shirt_Collected']=='Yes'))
                    if not row['T_Shirt_Collected']=='Yes':
                        c2.caption(f"Stock: {rem}")
                    
                    # Food Toggle
                    is_food = c3.toggle("🍔 Meal", value=(row['Food_Collected']=='Yes'))
                    
                    if st.button("💾 UPDATE STATUS", type="primary", use_container_width=True):
                        # Logic
                        # 1. Entry
                        st.session_state.df.at[row_idx, 'Entry_Status'] = 'Done' if is_entered else ''
                        if is_entered and not row['Entry_Time']:
                            st.session_state.df.at[row_idx, 'Entry_Time'] = datetime.now().strftime("%H:%M:%S")
                        
                        # 2. Kit Stock
                        if is_kit and row['T_Shirt_Collected'] == 'No':
                            st.session_state.stock[sz] -= 1
                            save_inv()
                        elif not is_kit and row['T_Shirt_Collected'] == 'Yes':
                            st.session_state.stock[sz] += 1
                            save_inv()
                        st.session_state.df.at[row_idx, 'T_Shirt_Collected'] = 'Yes' if is_kit else 'No'
                        
                        # 3. Food
                        st.session_state.df.at[row_idx, 'Food_Collected'] = 'Yes' if is_food else 'No'
                        
                        save_db()
                        add_log(f"Updated status for {row['Name']}")
                        st.success("Record Updated Successfully!")
                        st.rerun()

                # 5.4 Admin Edit (Full Control)
                if st.session_state.user_role == 'admin':
                    with st.expander("🛠️ Advanced Edit (Admin Only)"):
                        with st.form("edit_form"):
                            en = st.text_input("Name", row['Name'])
                            et = st.text_input("Ticket", row['Ticket_Number'])
                            ep = st.text_input("Phone", row['Spot Phone'])
                            eg = st.text_input("Guardian", row['Guardian Phone'])
                            er = st.selectbox("Role", ["Student", "Volunteer", "Teacher", "Guest"], index=["Student", "Volunteer", "Teacher", "Guest"].index(row['Role']) if row['Role'] in ["Student", "Volunteer", "Teacher", "Guest"] else 0)
                            eb = st.selectbox("Bus", ["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"], index=["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"].index(row['Bus_Number']) if row['Bus_Number'] in ["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"] else 0)
                            
                            if st.form_submit_button("Save Changes"):
                                st.session_state.df.at[row_idx, 'Name'] = en
                                st.session_state.df.at[row_idx, 'Ticket_Number'] = et
                                st.session_state.df.at[row_idx, 'Spot Phone'] = ep
                                st.session_state.df.at[row_idx, 'Guardian Phone'] = eg
                                st.session_state.df.at[row_idx, 'Role'] = er
                                st.session_state.df.at[row_idx, 'Bus_Number'] = eb
                                save_db()
                                add_log(f"Admin edited profile of {en}")
                                st.success("Profile Updated")
                                st.rerun()
        else:
            st.info("👋 Waiting for input... Scan or Type to begin.")

# ==============================================================================
# 6. MODULE: TEACHERS
# ==============================================================================
elif menu == "👨‍🏫 Teachers":
    st.title("👨‍🏫 Faculty Management")
    teachers = st.session_state.df[st.session_state.df['Role']=='Teacher']
    
    c1, c2 = st.columns(2)
    c1.metric("Total Faculty", len(teachers))
    c2.metric("Present", len(teachers[teachers['Entry_Status']=='Done']))
    
    st.markdown("---")
    
    # Quick Card View
    for i, (idx, row) in enumerate(teachers.iterrows()):
        with st.container(border=True):
            cols = st.columns([3, 1, 1, 1])
            cols[0].markdown(f"**{row['Name']}** <br> 📞 {row['Spot Phone']}", unsafe_allow_html=True)
            cols[1].info(f"Bus: {row['Bus_Number']}")
            
            # Actions
            if cols[2].button("✅ Check In", key=f"t_ent_{i}", disabled=(row['Entry_Status']=='Done')):
                st.session_state.df.at[idx, 'Entry_Status'] = 'Done'
                st.session_state.df.at[idx, 'Entry_Time'] = datetime.now().strftime("%H:%M:%S")
                save_db()
                st.rerun()
                
            if cols[3].button("👕 Give Kit", key=f"t_kit_{i}", disabled=(row['T_Shirt_Collected']=='Yes')):
                st.session_state.df.at[idx, 'T_Shirt_Collected'] = 'Yes'
                st.session_state.stock[row['T_Shirt_Size']] -= 1
                save_db()
                save_inv()
                st.rerun()

# ==============================================================================
# 7. MODULE: SMART TRANSPORT
# ==============================================================================
elif menu == "🚌 Smart Transport":
    st.title("🚌 Fleet Control")
    
    # Visual Bus Meter
    buses = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    cols = st.columns(4)
    
    for i, bus in enumerate(buses):
        count = len(st.session_state.df[st.session_state.df['Bus_Number'] == bus])
        percent = min(count/BUS_CAPACITY, 1.0)
        color = "green" if percent < 0.8 else "orange" if percent < 1.0 else "red"
        
        with cols[i]:
            st.markdown(f"**{bus}**")
            st.progress(percent)
            st.caption(f"{count} / {BUS_CAPACITY} Seats")
            if count > BUS_CAPACITY: st.error("OVERFLOW")
    
    st.markdown("---")
    
    # Smart Assign
    with st.expander("🚀 Smart Auto-Assign Tool", expanded=True):
        c1, c2, c3 = st.columns(3)
        mode = c1.selectbox("Filter By", ["Role", "Class"])
        
        opts = []
        if mode == "Role": opts = ["Student", "Volunteer", "Teacher"]
        else: opts = sorted(st.session_state.df['Class'].unique().tolist())
        
        group = c2.selectbox("Select Group", ["Select..."] + opts)
        start_bus = c3.selectbox("Starting Bus", buses)
        
        if st.button("Start Assignment Sequence", type="primary"):
            if group == "Select...": st.error("Select group!")
            else:
                mask = st.session_state.df['Role'] == group if mode == "Role" else st.session_state.df['Class'] == group
                indices = st.session_state.df[mask].index.tolist()
                
                curr_idx = buses.index(start_bus)
                assigned = 0
                
                for pid in indices:
                    # Find bus with space
                    while curr_idx < len(buses):
                        bus_name = buses[curr_idx]
                        if len(st.session_state.df[st.session_state.df['Bus_Number'] == bus_name]) < BUS_CAPACITY:
                            st.session_state.df.at[pid, 'Bus_Number'] = bus_name
                            assigned += 1
                            break
                        else:
                            curr_idx += 1 # Move to next bus
                
                save_db()
                add_log(f"Auto-assigned {assigned} people from {group}")
                st.success(f"Logistics Updated: {assigned} Assigned")
                st.rerun()
                
    if st.button("⚠️ Emergency Unassign Group"):
         if group != "Select...":
             mask = st.session_state.df['Role'] == group if mode == "Role" else st.session_state.df['Class'] == group
             st.session_state.df.loc[mask, 'Bus_Number'] = 'Unassigned'
             save_db()
             st.warning("Unassigned Complete")
             st.rerun()

    # Manifests
    st.markdown("### 📋 Manifests")
    tabs = st.tabs(["Unassigned"] + buses)
    with tabs[0]:
        st.dataframe(st.session_state.df[st.session_state.df['Bus_Number'].isin(['Unassigned', ''])][['Name', 'Role', 'Spot Phone']])
    for i, bus in enumerate(buses):
        with tabs[i+1]:
            st.dataframe(st.session_state.df[st.session_state.df['Bus_Number'] == bus][['Name', 'Role', 'Class']])

# ==============================================================================
# 8. MODULE: INVENTORY
# ==============================================================================
elif menu == "📦 Inventory (Kit/Food)":
    st.title("📦 Supply Chain")
    
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("👕 T-Shirt Stock")
        cols = st.columns(5)
        for s in ["S", "M", "L", "XL", "XXL"]:
            cols[cols.index(cols[0])+["S", "M", "L", "XL", "XXL"].index(s)].metric(s, st.session_state.stock.get(s, 0))
        
        with st.form("stock_adj"):
            sz = st.selectbox("Select Size", ["S", "M", "L", "XL", "XXL"])
            qty = st.number_input("Set New Quantity", 0)
            if st.form_submit_button("Update Stock"):
                st.session_state.stock[sz] = qty
                save_inv()
                add_log(f"Stock updated for {sz} to {qty}")
                st.rerun()
                
    with c2:
        st.subheader("🍔 Food Counter")
        served = len(st.session_state.df[st.session_state.df['Food_Collected']=='Yes'])
        total = len(st.session_state.df)
        st.metric("Meals Served", served, f"{total-served} Remaining")
        st.progress(served/total if total else 0)

# ==============================================================================
# 9. MODULE: ANALYTICS
# ==============================================================================
elif menu == "📊 Analytics":
    st.title("📊 Deep Dive Analytics")
    
    tab1, tab2, tab3 = st.tabs(["👥 Demographics", "🚌 Logistics", "👕 Sizes"])
    
    with tab1:
        # Role Distribution
        chart = alt.Chart(st.session_state.df).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Role", type="nominal", aggregate="count"),
            color=alt.Color(field="Role", type="nominal"),
            tooltip=["Role", "count()"]
        ).properties(title="Attendee Roles")
        st.altair_chart(chart, use_container_width=True)
        
    with tab2:
        # Bus Distribution
        chart = alt.Chart(st.session_state.df).mark_bar().encode(
            x='Bus_Number',
            y='count()',
            color='Bus_Number'
        ).properties(title="Bus Occupancy")
        st.altair_chart(chart, use_container_width=True)
        
    with tab3:
        # Size Demand
        chart = alt.Chart(st.session_state.df).mark_bar().encode(
            x='T_Shirt_Size',
            y='count()',
            color='T_Shirt_Size'
        )
        st.altair_chart(chart, use_container_width=True)

# ==============================================================================
# 10. MODULE: ADMIN & EXPORT
# ==============================================================================
elif menu == "⚙️ Admin & Logs":
    st.title("⚙️ System Administration")
    
    tab1, tab2 = st.tabs(["📜 Audit Logs", "📥 Export Center"])
    
    with tab1:
        st.write("Recent system activities:")
        for log in st.session_state.logs:
            st.text(log)
            
    with tab2:
        st.subheader("📄 Printable Manifests")
        st.caption("Includes 'In' and 'Out' signature columns.")
        
        # HTML Generator
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: sans-serif; }
                h1 { text-align: center; border-bottom: 2px solid #000; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid #333; padding: 8px; text-align: left; font-size: 12px; }
                th { background-color: #eee; }
                .page-break { page-break-before: always; }
                .sig-box { width: 100px; }
            </style>
        </head>
        <body>
        """
        
        for bus in ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]:
            bdf = st.session_state.df[st.session_state.df['Bus_Number']==bus]
            if not bdf.empty:
                if bus != "Bus 1": html += '<div class="page-break"></div>'
                html += f"<h1>{bus} MANIFEST</h1>"
                html += f"<p>Count: {len(bdf)}</p>"
                html += "<table><tr><th>#</th><th>Name</th><th>Role</th><th>Phone</th><th>Guardian</th><th class='sig-box'>IN Sign</th><th class='sig-box'>OUT Sign</th></tr>"
                for i, (_, r) in enumerate(bdf.iterrows(), 1):
                    html += f"<tr><td>{i}</td><td>{r['Name']}</td><td>{r['Role']}</td><td>{r['Spot Phone']}</td><td>{r['Guardian Phone']}</td><td></td><td></td></tr>"
                html += "</table>"
        
        html += "</body></html>"
        
        c1, c2 = st.columns(2)
        c1.download_button("📄 Download PDF Manifest", html, "Manifest.html", "text/html")
        c2.download_button("💾 Backup Database (CSV)", st.session_state.df.to_csv(), "Backup.csv", "text/csv")
