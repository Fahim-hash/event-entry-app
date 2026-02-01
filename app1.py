import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time
import altair as alt

# ==============================================================================
# 0. SYSTEM CONFIGURATION & UI STYLING
# ==============================================================================
st.set_page_config(page_title="Event OS Ultimate", page_icon="⚡", layout="wide")

# Custom UI/UX Styling
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    
    /* Neon Metric Cards */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(15px);
        border-radius: 15px; padding: 20px; border: 1px solid rgba(0, 255, 255, 0.1);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
    }
    
    /* Glassmorphism ID Card */
    .id-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 25px; padding: 30px;
        color: #fff; text-align: center;
        box-shadow: 0 25px 50px rgba(0,0,0,0.6);
        margin-bottom: 20px;
    }
    
    .id-header { 
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        padding: 12px; border-radius: 15px; font-weight: 800; letter-spacing: 1px;
    }
    
    .id-role-badge { 
        background: #ffcc00; color: #000; padding: 4px 18px; border-radius: 50px; 
        font-size: 13px; font-weight: 900; margin-top: 15px; display: inline-block;
        box-shadow: 0 0 15px rgba(255, 204, 0, 0.4);
    }
    
    .id-name { font-size: 32px; font-weight: 900; margin: 15px 0; text-shadow: 0 0 10px rgba(255,255,255,0.3); }
    
    .id-info-row { 
        display: flex; justify-content: space-between; 
        border-bottom: 1px solid rgba(255,255,255,0.1); 
        padding: 8px 0; font-size: 15px; color: #bbb;
    }
    
    .tshirt-badge { 
        font-weight: 800; padding: 10px; border-radius: 10px; margin-top: 20px; 
        border: 1px solid rgba(255,255,255,0.2); text-align: center;
    }
    
    .notes-box { 
        background: rgba(255, 255, 255, 0.05); 
        border-left: 4px solid #ff4b4b; 
        padding: 10px; border-radius: 5px; 
        margin-top: 15px; font-style: italic; font-size: 14px; 
    }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 1. DATABASE & SESSION INITIALIZATION
# ==============================================================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'portal_user' not in st.session_state: st.session_state.portal_user = None
if 'logs' not in st.session_state: st.session_state.logs = []

def add_log(msg):
    t = datetime.now().strftime("%H:%M:%S")
    user = st.session_state.get('user_name', 'System')
    st.session_state.logs.insert(0, f"[{t}] {user}: {msg}")

BUS_CAPACITY = 45 #
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Data", ttl=0)
        # Ensure Schema for Reports and Feedback
        req_cols = ['Name', 'Role', 'Spot Phone', 'Guardian Phone', 'Ticket_Number', 
                    'Class', 'Roll', 'Entry_Status', 'Entry_Time', 'Bus_Number', 
                    'T_Shirt_Size', 'T_Shirt_Collected', 'Notes', 'Fault_Report', 'Image_URL']
        for c in req_cols:
            if c not in df.columns: df[c] = ''
        # Clean Data (Fix 2634.0)
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True).replace(['nan', 'None', ''], 'N/A')
        return df
    except: return pd.DataFrame()

def load_stock():
    try:
        df_s = conn.read(worksheet="Stock", ttl=0)
        stock = dict(zip(df_s['Size'], df_s['Quantity']))
        return {s: int(float(stock.get(s, 0))) for s in ["S", "M", "L", "XL", "XXL"]}
    except: return {"S":0, "M":0, "L":0, "XL":0, "XXL":0}

if 'df' not in st.session_state: st.session_state.df = load_data()
if 'stock' not in st.session_state: st.session_state.stock = load_stock()

# ==============================================================================
# 2. MULTI-PORTAL LOGIN TERMINAL
# ==============================================================================
def login_screen():
    st.markdown("<h1 style='text-align:center;'>⚡ Event OS Ultimate</h1>", unsafe_allow_html=True)
    tab_admin, tab_student = st.tabs(["🔐 Staff Terminal", "🎓 Student Portal"])
    
    with tab_admin:
        u = st.text_input("Username", key="admin_u")
        p = st.text_input("Password", type="password", key="admin_p")
        if st.button("Authenticate", use_container_width=True):
            USERS = {"admin": "1234", "gate": "entry26"}
            if u in USERS and USERS[u] == p:
                st.session_state.logged_in = True
                st.session_state.user_role = "admin" if u=="admin" else "gate"
                st.session_state.user_name = u
                st.rerun()
            else: st.error("Access Denied!")

    with tab_student:
        st.info("Log in using Ticket Number as ID and Spot Phone as Password.") #
        s_id = st.text_input("Ticket Number", key="s_id")
        s_pw = st.text_input("Spot Phone Number", type="password", key="s_pw")
        if st.button("Log In to Portal", type="primary", use_container_width=True):
            df = st.session_state.df
            # Match ticket and phone
            match = df[(df['Ticket_Number'] == s_id) & (df['Spot Phone'] == s_pw)]
            if not match.empty:
                st.session_state.portal_user = match.iloc[0]['Ticket_Number']
                st.rerun()
            else: st.error("Invalid Credentials! Please try again.")

if not st.session_state.logged_in and not st.session_state.portal_user:
    login_screen()
    st.stop()

# ==============================================================================
# 3. STUDENT PORTAL MODULE
# ==============================================================================
if st.session_state.portal_user:
    st.sidebar.title("🎓 My Portal")
    user_tick = st.session_state.portal_user
    user_data = st.session_state.df[st.session_state.df['Ticket_Number'] == user_tick].iloc[0]
    
    p_menu = st.sidebar.radio("Quick Actions", ["🏠 Digital ID", "🚩 Report a Fault", "📞 Contact Organisers"])
    
    if p_menu == "🏠 Digital ID":
        st.title(f"Hello, {user_data['Name']}!")
        st.markdown(f"""
        <div class="id-card">
            <div class="id-header">OFFICIAL STUDENT PASS</div>
            <div class="id-name">{user_data['Name']}</div>
            <div class="id-info-row"><span>Ticket No</span><span>{user_data['Ticket_Number']}</span></div>
            <div class="id-info-row"><span>Bus Assigned</span><span>{user_data['Bus_Number']}</span></div>
            <div class="id-info-row"><span>Check-In</span><span style="color:#00ff88;">{user_data['Entry_Status']}</span></div>
        </div>
        """, unsafe_allow_html=True)

    elif p_menu == "🚩 Report a Fault":
        st.header("Help Us Improve") #
        with st.form("student_feedback"):
            report = st.text_area("What is the issue or fault you've noticed?", placeholder="Submit our faults here...") #
            img = st.file_uploader("Upload Image (Optional)", type=['jpg','png','jpeg']) #
            if st.form_submit_button("Submit Report"):
                idx = st.session_state.df[st.session_state.df['Ticket_Number'] == user_tick].index[0]
                st.session_state.df.at[idx, 'Fault_Report'] = report
                conn.update(worksheet="Data", data=st.session_state.df)
                st.success("Your report has been submitted to the organisers.")

    elif p_menu == "📞 Contact Organisers":
        st.header("Direct Contact") #
        st.write("📞 **Admin Team:** +880 1XXXXXXXXX")
        st.write("🚌 **Transport Lead:** +880 1XXXXXXXXX")

    if st.sidebar.button("🚪 Exit Portal"):
        st.session_state.portal_user = None
        st.rerun()
    st.stop()

# ==============================================================================
# 4. STAFF TERMINAL (ADMIN/GATE)
# ==============================================================================
with st.sidebar:
    st.title("⚡ OS Terminal")
    st.write(f"Session: **{st.session_state.user_role.upper()}**")
    nav = st.radio("Navigation", ["🏠 Dashboard", "🔍 Search & Access", "👨‍🏫 Teachers", "🚌 Smart Fleet", "📦 Inventory", "📊 Analytics", "⚙️ Admin Logs"])
    
    if st.button("🔄 Sync Cloud Data", use_container_width=True):
        st.cache_data.clear()
        st.session_state.df = load_data()
        st.session_state.stock = load_stock()
        st.rerun()
    if st.button("🚪 Logout Terminal", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# --- MODULE: DASHBOARD ---
if nav == "🏠 Dashboard":
    st.title("🚀 Event Overview")
    df = st.session_state.df
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Registered", len(df))
    c2.metric("Checked In", len(df[df['Entry_Status'] == 'Done']))
    c3.metric("Kits Given", len(df[df['T_Shirt_Collected'] == 'Yes']))
    reports = len(df[df['Fault_Report'] != 'N/A'])
    c4.metric("Active Reports", reports, delta="Attention Required" if reports > 0 else "")
    
    st.subheader("Live Entry Log")
    st.dataframe(df[df['Entry_Status']=='Done'].sort_values('Entry_Time', ascending=False).head(10)[['Name', 'Role', 'Entry_Time', 'Bus_Number']], use_container_width=True)

# --- MODULE: SEARCH & ACCESS (Visuals + Full Edit + Unassign) ---
elif nav == "🔍 Search & Access":
    st.title("🔍 Access Management")
    q = st.text_input("Enter Name / Ticket / Phone:").strip()
    
    if q:
        df = st.session_state.df
        mask = df['Name'].str.contains(q, case=False) | df['Ticket_Number'].str.contains(q, case=False) | df['Spot Phone'].str.contains(q, case=False)
        res = df[mask]
        
        if not res.empty:
            idx = res.index[0]
            row = df.loc[idx]
            qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={row['Ticket_Number']}" #
            
            is_ent = row['Entry_Status'] == 'Done'
            c_color = "#00ff88" if is_ent else "#ff4b4b"
            
            # Kit Logic
            sz = row['T_Shirt_Size']
            rem = st.session_state.stock.get(sz, 0)
            is_kit = row['T_Shirt_Collected'] == 'Yes'
            if is_kit: kit_html = f'<div class="tshirt-badge" style="color:#00ff88; border-color:#00ff88;">👕 {sz} : GIVEN ✅</div>'
            elif rem > 0: kit_html = f'<div class="tshirt-badge" style="color:#00c6ff; border-color:#00c6ff;">👕 {sz} : IN STOCK ({rem}) 📦</div>'
            else: kit_html = f'<div class="tshirt-badge" style="color:#ff4b4b; border-color:#ff4b4b;">👕 {sz} : OUT OF STOCK ❌</div>'

            col1, col2 = st.columns([1, 1.5])
            with col1:
                st.markdown(f"""
                <div class="id-card" style="border: 2px solid {c_color};">
                <div class="id-header" style="background:{c_color};">{'PASS VERIFIED' if is_ent else 'PENDING ENTRY'}</div>
                <div class="id-role-badge">{row['Role'].upper()}</div>
                <div class="id-name">{row['Name']}</div>
                <div class="id-info-row"><span>Ticket</span><span>{row['Ticket_Number']}</span></div>
                <div class="id-info-row"><span>Bus</span><span>{row['Bus_Number']}</span></div>
                {kit_html}
                <div class="notes-box">📝 Notes: {row['Notes']}</div>
                <div style="background: white; padding: 10px; border-radius: 10px; display: inline-block; margin-top: 15px;"><img src="{qr_api}" width="100"></div>
                </div>
                """, unsafe_allow_html=True)
                
                if row['Fault_Report'] != 'N/A':
                    st.error(f"⚠️ Student Report: {row['Fault_Report']}")

            with col2:
                with st.form("profile_update_form"):
                    st.subheader("📝 Edit Profile & Update Status") #
                    ca, cb = st.columns(2)
                    e_name = ca.text_input("Full Name", row['Name'])
                    e_phone = cb.text_input("Spot Phone (Required for Entry)", row['Spot Phone'])
                    
                    cc, cd = st.columns(2)
                    e_tick = cc.text_input("Ticket Number (Required for Entry)", row['Ticket_Number'])
                    e_roll = cd.text_input("Roll No", row['Roll'])
                    
                    st.markdown("---")
                    ce, cf = st.columns(2)
                    e_ent = ce.toggle("Check-In Accomplished", value=is_ent)
                    e_kit = cf.toggle("Merchandise Given", value=is_kit)
                    
                    sizes = ["S", "M", "L", "XL", "XXL"]
                    e_size = st.selectbox("Update Merchandise Size", sizes, index=sizes.index(sz) if sz in sizes else 2) #
                    e_notes = st.text_area("Internal Staff Notes", value=row['Notes'] if row['Notes'] != 'N/A' else "") #
                    
                    if st.form_submit_button("💾 Save Profile Changes"):
                        # Verification check
                        if e_ent and (e_phone in ['N/A', ''] or e_tick in ['N/A', '']):
                            st.error("❌ Spot Phone and Ticket Number are REQUIRED to grant entry!")
                        else:
                            # Inventory Logic
                            if e_kit and not is_kit: st.session_state.stock[e_size] -= 1
                            elif not e_kit and is_kit: st.session_state.stock[sz] += 1
                            
                            st.session_state.df.at[idx, 'Name'] = e_name
                            st.session_state.df.at[idx, 'Spot Phone'] = e_phone
                            st.session_state.df.at[idx, 'Ticket_Number'] = e_tick
                            st.session_state.df.at[idx, 'Roll'] = e_roll
                            st.session_state.df.at[idx, 'Entry_Status'] = 'Done' if e_ent else 'N/A'
                            st.session_state.df.at[idx, 'T_Shirt_Collected'] = 'Yes' if e_kit else 'No'
                            st.session_state.df.at[idx, 'T_Shirt_Size'] = e_size
                            st.session_state.df.at[idx, 'Notes'] = e_notes
                            if e_ent and row['Entry_Time'] == 'N/A': st.session_state.df.at[idx, 'Entry_Time'] = datetime.now().strftime("%H:%M:%S")
                            
                            conn.update(worksheet="Data", data=st.session_state.df)
                            # Update Stock Sheet
                            data_stock = [{"Size": k, "Quantity": v} for k, v in st.session_state.stock.items()]
                            conn.update(worksheet="Stock", data=pd.DataFrame(data_stock))
                            add_log(f"Synced changes for {e_name}")
                            st.success("Successfully Synchronized!"); time.sleep(0.5); st.rerun()

                # Dashboard Unassign Logic
                if row['Bus_Number'] != 'Unassigned':
                    if st.button("❌ UNASSIGN BUS IMMEDIATELY", type="secondary", use_container_width=True):
                        st.session_state.df.at[idx, 'Bus_Number'] = 'Unassigned'
                        conn.update(worksheet="Data", data=st.session_state.df)
                        add_log(f"Canceled bus assignment for {row['Name']}")
                        st.rerun()
        else: st.warning("No records found.")

# --- MODULE: SMART FLEET (Overflow + Class Assign) ---
elif nav == "🚌 Smart Fleet":
    st.title("🚌 Fleet Logistics Control")
    buses = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    cols = st.columns(4)
    for i, b in enumerate(buses):
        num = len(st.session_state.df[st.session_state.df['Bus_Number'] == b])
        cols[i].metric(b, f"{num}/{BUS_CAPACITY}", f"{BUS_CAPACITY-num} Free")
        cols[i].progress(min(num/BUS_CAPACITY, 1.0))
    
    st.markdown("---")
    with st.expander("🚀 Smart Auto-Fill Logic (Role or Class)"): #
        ca, cb, cc = st.columns(3)
        mode = ca.selectbox("Assign By", ["Class", "Role"])
        val = cb.selectbox("Target Group", sorted(st.session_state.df[mode].unique()))
        start = cc.selectbox("Start From", buses)
        
        if st.button("Initiate Assignment Sequence"):
            p_indices = st.session_state.df[st.session_state.df[mode] == val].index.tolist()
            b_idx = buses.index(start)
            for p_idx in p_indices:
                while b_idx < 4:
                    if len(st.session_state.df[st.session_state.df['Bus_Number'] == buses[b_idx]]) < BUS_CAPACITY:
                        st.session_state.df.at[p_idx, 'Bus_Number'] = buses[b_idx]
                        break
                    else: b_idx += 1 # Overflow logic
            conn.update(worksheet="Data", data=st.session_state.df)
            st.success("Logistics Updated!"); st.rerun()

# --- MODULE: ADMIN LOGS & EXPORT (Printable Manifest) ---
elif nav == "⚙️ Admin Logs":
    st.title("⚙️ System Administration")
    t1, t2 = st.tabs(["📜 System Activity", "📥 Manifest Export"])
    with t1:
        for entry in st.session_state.logs: st.text(entry)
    with t2:
        if st.button("📄 Generate Signature-Ready Bus Manifest"): #
            html = "<html><head><meta charset='UTF-8'></head><body><h1>Bus Manifest - SIGNATURE LIST</h1>"
            for b in ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]:
                b_df = st.session_state.df[st.session_state.df['Bus_Number'] == b]
                if not b_df.empty:
                    html += f"<h2>{b} - Pass List</h2><table border='1' width='100%'><tr><th>Sl.</th><th>Class</th><th>Name</th><th>Ticket</th><th>In Sign</th><th>Out Sign</th></tr>"
                    for j, (_, r) in enumerate(b_df.iterrows(), 1):
                        html += f"<tr><td>{j}</td><td>{r['Class']}</td><td>{r['Name']}</td><td>{r['Ticket_Number']}</td><td width='80'></td><td width='80'></td></tr>"
                    html += "</table><br>"
            html += "</body></html>"
            st.download_button("Download Print-Ready Manifest", html, "Bus_Manifest.html", "text/html")

# --- OTHER MODULES ---
elif nav == "👨‍🏫 Teachers":
    st.title("👨‍🏫 Faculty Control")
    st.dataframe(st.session_state.df[st.session_state.df['Role'] == 'Teacher'], use_container_width=True)

elif nav == "📦 Inventory":
    st.title("📦 T-Shirt Inventory Status")
    cols = st.columns(5)
    for i, s in enumerate(["S", "M", "L", "XL", "XXL"]):
        cols[i].metric(s, st.session_state.stock.get(s, 0))
