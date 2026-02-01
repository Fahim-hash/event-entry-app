import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# ==================== 0. PAGE CONFIG & CUSTOM CSS ====================
st.set_page_config(page_title="Event Manager Pro", page_icon="🔥", layout="wide")

# Custom CSS for "Joss" Look
st.markdown("""
    <style>
    /* Dark Theme Optimization */
    .stApp {background-color: #0e1117;}
    
    /* Search Bar Styling */
    input[type="text"] {
        border-radius: 10px !important;
        border: 1px solid #3b3f4a !important;
        padding: 10px !important;
    }
    
    /* Metrics Card Styling */
    div[data-testid="stMetric"] {
        background-color: #1e2129;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #ff4b4b;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Digital ID Card Styling */
    .id-card {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); /* Royal Gradient */
        padding: 25px;
        border-radius: 15px;
        color: #fff;
        text-align: center;
        font-family: 'Arial', sans-serif;
        box-shadow: 0 10px 20px rgba(0,0,0,0.5);
        border: 1px solid #45a29e;
        margin-bottom: 20px;
    }
    .id-role {
        background-color: #ffcc00;
        color: #000;
        padding: 5px 20px;
        border-radius: 50px;
        font-weight: 900;
        text-transform: uppercase;
        font-size: 14px;
        display: inline-block;
        margin-bottom: 10px;
        box-shadow: 0 0 10px #ffcc00;
    }
    .id-name { font-size: 28px; font-weight: bold; margin: 10px 0; text-shadow: 2px 2px 4px #000; }
    .id-info { font-size: 16px; margin: 6px 0; color: #c5c6c7; }
    .status-badge {
        margin-top: 15px;
        font-size: 18px;
        font-weight: bold;
        padding: 8px;
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== 1. LOGIN SYSTEM ====================
USERS = {
    "admin": {"password": "1234", "role": "admin", "name": "Super Admin"},
    "gate": {"password": "entry26", "role": "volunteer", "name": "Gate Volunteer"}
}

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def check_login():
    user = st.session_state['username']
    pwd = st.session_state['password']
    if user in USERS and USERS[user]["password"] == pwd:
        st.session_state.logged_in = True
        st.session_state.user_role = USERS[user]["role"]
        st.session_state.user_name = USERS[user]["name"]
        st.success("Access Granted! 🚀")
        st.rerun()
    else:
        st.error("❌ ভুল ইউজারনেম বা পাসওয়ার্ড!")

if not st.session_state.logged_in:
    st.title("🔒 Event Manager Pro")
    c1, c2 = st.columns([1, 2])
    with c1: st.markdown("# 🔐")
    with c2:
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("🚀 Login", on_click=check_login, type="primary", use_container_width=True)
    st.stop()

# ==================== 2. DATA ENGINE (SEARCH FIX) ====================
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Data", ttl=0)
        cols = ['Name', 'Role', 'Spot Phone', 'Ticket_Number', 'Class', 'Roll', 'Entry_Status', 'Entry_Time', 'Bus_Number', 'T_Shirt_Size', 'T_Shirt_Collected', 'Notes']
        for c in cols:
            if c not in df.columns: df[c] = ''
        
        # 🔥 CRITICAL SEARCH FIX: FORCE EVERYTHING TO STRING 🔥
        df['Ticket_Number'] = df['Ticket_Number'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        df['Spot Phone'] = df['Spot Phone'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        df['Roll'] = df['Roll'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        df = df.fillna('')
        return df
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        return pd.DataFrame(columns=['Name', 'Role', 'Ticket_Number'])

def load_stock():
    try:
        df_s = conn.read(worksheet="Stock", ttl=0)
        stock = dict(zip(df_s['Size'], df_s['Quantity']))
        for s in ["S", "M", "L", "XL", "XXL"]: 
            if s not in stock: stock[s] = 0
        return stock
    except: return {"S":0, "M":0, "L":0, "XL":0, "XXL":0}

if 'df' not in st.session_state: st.session_state.df = load_data()
if 'stock' not in st.session_state: st.session_state.stock = load_stock()

def save_data():
    try: conn.update(worksheet="Data", data=st.session_state.df)
    except: st.error("Save Failed!")

def save_stock():
    try:
        data = [{"Size": k, "Quantity": v} for k, v in st.session_state.stock.items()]
        conn.update(worksheet="Stock", data=pd.DataFrame(data))
    except: st.error("Stock Save Failed!")

# ==================== 3. APP NAVIGATION ====================

st.sidebar.markdown(f"## 👋 Hi, {st.session_state.user_name}")
st.sidebar.caption(f"Role: {st.session_state.user_role.upper()}")

if st.sidebar.button("🔄 Force Refresh Data", type="primary"):
    st.cache_data.clear()
    st.session_state.df = load_data()
    st.session_state.stock = load_stock()
    st.success("Data Refreshed!")
    st.rerun()

menu_opts = ["🏠 Dashboard", "🔍 Search & Manage", "📊 Analytics"]
if st.session_state.user_role == 'admin':
    menu_opts += ["📦 Stock", "🚌 Bus Fleet", "📥 Export"]

menu = st.sidebar.radio("Menu:", menu_opts)

# ADD PERSON SHORTCUT
if st.session_state.user_role == 'admin':
    st.sidebar.markdown("---")
    with st.sidebar.expander("➕ Add Person"):
        with st.form("add_fast"):
            n = st.text_input("Name")
            r = st.selectbox("Role", ["Student", "Volunteer", "Organizer", "Teacher", "Guest"])
            p = st.text_input("Phone")
            t = st.text_input("Ticket")
            if st.form_submit_button("Add Now"):
                if n and p and t:
                    new = {'Name': n, 'Role': r, 'Spot Phone': str(p), 'Ticket_Number': str(t), 'Class': 'New', 'Roll': '', 'Entry_Status': '', 'Bus_Number': 'Unassigned', 'T_Shirt_Size': 'L', 'T_Shirt_Collected': 'No', 'Notes': 'Added'}
                    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new])], ignore_index=True)
                    save_data()
                    st.success("Added!")
                    st.rerun()
                else: st.error("Missing Info!")

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# ==================== 4. MAIN FEATURES ====================

# --- DASHBOARD ---
if menu == "🏠 Dashboard":
    st.title("🚀 Event Control Center")
    df = st.session_state.df
    
    # Live Counters
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total People", len(df), "Registered")
    c2.metric("Checked In", len(df[df['Entry_Status']=='Done']), "People Inside")
    c3.metric("T-Shirts Out", len(df[df['T_Shirt_Collected']=='Yes']), "Distributed")
    c4.metric("Pending", len(df[df['Entry_Status']!='Done']), "Outside")
    
    st.progress(len(df[df['Entry_Status']=='Done']) / len(df) if len(df) > 0 else 0)
    
    # Recent Activity
    st.subheader("📡 Live Feed (Last 5 Entries)")
    recent = df[df['Entry_Status']=='Done'].sort_values('Entry_Time', ascending=False).head(5)
    st.dataframe(recent[['Name', 'Role', 'Entry_Time', 'Bus_Number']], use_container_width=True)

# --- SEARCH & MANAGE (THE CORE) ---
elif menu == "🔍 Search & Manage":
    st.title("🔍 Search & Digital ID")
    
    # SEARCH BAR
    q = st.text_input("🔎 Search by Ticket / Name / Phone / Roll:", placeholder="Type anything...").strip()
    
    if q:
        # Powerful Search Logic (Case Insensitive + String conversion)
        mask = (
            st.session_state.df['Name'].astype(str).str.contains(q, case=False) |
            st.session_state.df['Ticket_Number'].astype(str).str.contains(q, case=False) |
            st.session_state.df['Spot Phone'].astype(str).str.contains(q, case=False) |
            st.session_state.df['Roll'].astype(str).str.contains(q, case=False)
        )
        res = st.session_state.df[mask]
        
        if not res.empty:
            # Selector if multiple results
            idx = res.index[0]
            if len(res) > 1:
                st.info(f"Found {len(res)} matches!")
                sel = st.selectbox("Select Person:", res['Name'].tolist())
                idx = res[res['Name'] == sel].index[0]
            
            row = st.session_state.df.loc[idx]
            
            # DIGITAL ID CARD UI
            col_card, col_action = st.columns([1, 1.5])
            
            with col_card:
                st.markdown(f"""
                <div class="id-card">
                    <div class="id-role">{row['Role'].upper()}</div>
                    <div class="id-name">{row['Name']}</div>
                    <div class="id-info">🎟 Ticket: <b>{row['Ticket_Number']}</b></div>
                    <div class="id-info">🆔 Roll: {row['Roll']}</div>
                    <div class="id-info">📞 {row['Spot Phone']}</div>
                    <div class="id-info">🚌 Bus: {row['Bus_Number']}</div>
                    <div class="status-badge" style="color: {'#4ade80' if row['Entry_Status']=='Done' else '#f87171'}; border: 1px solid {'#4ade80' if row['Entry_Status']=='Done' else '#f87171'};">
                        {'✅ CHECKED IN' if row['Entry_Status']=='Done' else '⏳ NOT ENTERED'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # ACTION PANEL
            with col_action:
                with st.container(border=True):
                    st.subheader("⚡ Quick Actions")
                    c1, c2 = st.columns(2)
                    
                    # Status Toggles
                    new_ent = c1.checkbox("✅ Mark Entry", value=(row['Entry_Status']=='Done'), key="ent")
                    new_tsh = c2.checkbox("👕 T-Shirt Given", value=(row['T_Shirt_Collected']=='Yes'), key="tsh")
                    
                    if st.button("💾 Save Status", type="primary", use_container_width=True):
                        # Save Entry
                        st.session_state.df.at[idx, 'Entry_Status'] = 'Done' if new_ent else ''
                        if new_ent and not row['Entry_Time']:
                            st.session_state.df.at[idx, 'Entry_Time'] = datetime.now().strftime("%H:%M:%S")
                        
                        # Save Stock Logic
                        sz = row['T_Shirt_Size']
                        if new_tsh and row['T_Shirt_Collected'] == 'No':
                            st.session_state.stock[sz] -= 1
                            save_stock()
                        elif not new_tsh and row['T_Shirt_Collected'] == 'Yes':
                            st.session_state.stock[sz] += 1
                            save_stock()
                        st.session_state.df.at[idx, 'T_Shirt_Collected'] = 'Yes' if new_tsh else 'No'
                        
                        save_data()
                        st.success("Updated!")
                        time.sleep(0.5)
                        st.rerun()

                # --- SUPER EDIT FORM (ADMIN ONLY) ---
                if st.session_state.user_role == 'admin':
                    with st.expander("📝 Edit Full Profile (Admin)", expanded=False):
                        with st.form("super_edit"):
                            c_a, c_b = st.columns(2)
                            e_name = c_a.text_input("Name", row['Name'])
                            e_phone = c_b.text_input("Phone", row['Spot Phone'])
                            
                            c_c, c_d = st.columns(2)
                            e_ticket = c_c.text_input("Ticket No", row['Ticket_Number'])
                            e_roll = c_d.text_input("Roll / ID", row['Roll'])
                            
                            c_e, c_f = st.columns(2)
                            # Role Edit
                            roles = ["Student", "Volunteer", "Organizer", "Teacher", "Guest"]
                            curr_role = row['Role'] if row['Role'] in roles else "Student"
                            e_role = c_e.selectbox("Role", roles, index=roles.index(curr_role))
                            
                            # Bus Edit
                            buses = ["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"]
                            curr_bus = row['Bus_Number'] if row['Bus_Number'] in buses else "Unassigned"
                            e_bus = c_f.selectbox("Bus", buses, index=buses.index(curr_bus))
                            
                            e_size = st.selectbox("T-Shirt Size", ["S", "M", "L", "XL", "XXL"], index=["S", "M", "L", "XL", "XXL"].index(row['T_Shirt_Size']))
                            
                            if st.form_submit_button("💾 Save All Changes"):
                                if not e_ticket or not e_phone:
                                    st.error("Ticket and Phone cannot be empty!")
                                else:
                                    st.session_state.df.at[idx, 'Name'] = e_name
                                    st.session_state.df.at[idx, 'Spot Phone'] = str(e_phone)
                                    st.session_state.df.at[idx, 'Ticket_Number'] = str(e_ticket)
                                    st.session_state.df.at[idx, 'Roll'] = str(e_roll)
                                    st.session_state.df.at[idx, 'Role'] = e_role
                                    st.session_state.df.at[idx, 'Bus_Number'] = e_bus
                                    st.session_state.df.at[idx, 'T_Shirt_Size'] = e_size
                                    save_data()
                                    st.success("Profile Updated!")
                                    st.rerun()
        else:
            st.warning("No matches found! Try a different number or name.")

# --- ANALYTICS ---
elif menu == "📊 Analytics":
    st.title("📊 Visual Analytics")
    t1, t2 = st.tabs(["🚌 Transport", "👕 Merchandise"])
    with t1:
        st.bar_chart(st.session_state.df['Bus_Number'].value_counts())
    with t2:
        st.bar_chart(st.session_state.df['T_Shirt_Size'].value_counts())

# --- STOCK MANAGER ---
elif menu == "📦 Stock":
    st.title("📦 Inventory")
    cols = st.columns(5)
    for s in ["S", "M", "L", "XL", "XXL"]:
        q = st.session_state.stock.get(s, 0)
        cols[cols.index(cols[0])+["S", "M", "L", "XL", "XXL"].index(s)].metric(s, q)
    
    with st.form("upd_stk"):
        c1, c2 = st.columns(2)
        sz = c1.selectbox("Size", ["S", "M", "L", "XL", "XXL"])
        nq = c2.number_input("New Qty", 0)
        if st.form_submit_button("Update"):
            st.session_state.stock[sz] = nq
            save_stock()
            st.rerun()

# --- BUS MANAGER ---
elif menu == "🚌 Bus Fleet":
    st.title("🚌 Fleet Manager")
    c1, c2, c3 = st.columns(3)
    grp = c1.selectbox("Role Group", ["Student", "Volunteer", "Teacher"])
    bus = c2.selectbox("Target Bus", ["Bus 1", "Bus 2", "Bus 3", "Bus 4"])
    if c3.button("Assign Group", type="primary"):
        mask = st.session_state.df['Role'] == grp
        st.session_state.df.loc[mask, 'Bus_Number'] = bus
        save_data()
        st.success("Bulk Assigned!")
        st.rerun()
    st.dataframe(st.session_state.df[['Name', 'Role', 'Bus_Number']])

# --- EXPORT ---
elif menu == "📥 Export":
    st.title("📥 Download Data")
    csv = st.session_state.df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "Event_DB.csv", "text/csv")
