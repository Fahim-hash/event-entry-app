import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time
import altair as alt

# ==================== 0. SYSTEM CONFIG & UI STYLING ====================
st.set_page_config(page_title="Event OS Ultimate", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #e0e0e0; }
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border-radius: 15px; padding: 20px; border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .id-card {
        background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
        border: 2px solid #333; border-radius: 20px; padding: 20px;
        color: #fff; text-align: center; box-shadow: 0 20px 50px rgba(0,0,0,0.5);
    }
    .id-header { background: linear-gradient(90deg, #00c6ff, #0072ff); padding: 10px; border-radius: 10px; font-weight: bold; }
    .id-role-badge { background: #ffcc00; color: #000; padding: 3px 15px; border-radius: 50px; font-size: 12px; font-weight: 800; margin-top: 10px; display: inline-block; }
    .id-name { font-size: 28px; font-weight: 800; margin: 15px 0; }
    .id-info-row { display: flex; justify-content: space-between; border-bottom: 1px solid #333; padding: 5px 0; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# ==================== 1. LOGIN & AUDIT LOGS ====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'logs' not in st.session_state:
    st.session_state.logs = []

def add_log(msg):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, f"[{t}] {st.session_state.get('user_name', 'System')}: {msg}")

USERS = {
    "admin": {"password": "1234", "role": "admin", "name": "Super Admin"},
    "gate": {"password": "entry26", "role": "volunteer", "name": "Gate Officer"}
}

if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("⚡ Event OS Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Access Terminal", type="primary", use_container_width=True):
            if u in USERS and USERS[u]["password"] == p:
                st.session_state.logged_in = True
                st.session_state.user_role = USERS[u]["role"]
                st.session_state.user_name = USERS[u]["name"]
                st.rerun()
            else: st.error("❌ Invalid Access Key")
    st.stop()

# ==================== 2. DATA ENGINE ====================
BUS_CAPACITY = 45
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Data", ttl=0)
        req_cols = ['Name', 'Role', 'Spot Phone', 'Guardian Phone', 'Ticket_Number', 'Class', 'Roll', 'Entry_Status', 'Entry_Time', 'Bus_Number', 'T_Shirt_Size', 'T_Shirt_Collected']
        for c in req_cols:
            if c not in df.columns: df[c] = ''
        for col in df.columns:
            df[col] = df[col].astype(str).replace(['nan', 'None', ''], 'N/A')
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

# ==================== 3. NAVIGATION ====================
with st.sidebar:
    st.title("⚡ Event OS")
    st.write(f"Officer: **{st.session_state.user_name}**")
    menu = st.radio("Menu", ["🏠 Dashboard", "🔍 Search & Entry", "👨‍🏫 Teachers", "🚌 Smart Transport", "📦 Inventory", "📊 Analytics", "⚙️ Admin Logs"])
    
    if st.button("🔄 Sync Cloud", use_container_width=True):
        st.cache_data.clear()
        st.session_state.df = load_data()
        st.session_state.stock = load_stock()
        st.rerun()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# --- 4. MODULE: DASHBOARD ---
if menu == "🏠 Dashboard":
    st.title("🚀 Command Center")
    df = st.session_state.df
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Pax", len(df))
    c2.metric("Checked In", len(df[df['Entry_Status'] == 'Done']))
    c3.metric("Kits Given", len(df[df['T_Shirt_Collected'] == 'Yes']))
    st.progress(len(df[df['Entry_Status'] == 'Done']) / len(df) if len(df) > 0 else 0)
    
    st.subheader("📡 Live Activity Feed")
    st.dataframe(df[df['Entry_Status']=='Done'].sort_values('Entry_Time', ascending=False).head(10)[['Name', 'Role', 'Entry_Time', 'Bus_Number']], use_container_width=True)

# --- 5. MODULE: SEARCH & DIGITAL ID (With Dashboard Unassign) ---
elif menu == "🔍 Search & Entry":
    st.title("🔍 Access Terminal")
    q = st.text_input("Scan Ticket / Enter Phone / Name:").strip()
    
    if q:
        df = st.session_state.df
        mask = df['Name'].str.contains(q, case=False) | df['Ticket_Number'].str.contains(q, case=False) | df['Spot Phone'].str.contains(q, case=False)
        res = df[mask]
        
        if not res.empty:
            idx = res.index[0]
            row = df.loc[idx]
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={row['Ticket_Number']}"
            
            col1, col2 = st.columns([1, 1.5])
            with col1:
                st.markdown(f"""
                <div class="id-card">
                    <div class="id-header">OFFICIAL PASS</div>
                    <div class="id-role-badge">{row['Role'].upper()}</div>
                    <div class="id-name">{row['Name']}</div>
                    <div class="id-info-row"><span>Ticket</span><span>{row['Ticket_Number']}</span></div>
                    <div class="id-info-row"><span>Roll</span><span>{row['Roll']}</span></div>
                    <div class="id-info-row"><span>Phone</span><span>{row['Spot Phone']}</span></div>
                    <div class="id-info-row"><span>Bus</span><span>{row['Bus_Number']}</span></div>
                    <div style="background: white; padding: 10px; border-radius: 10px; display: inline-block; margin-top: 15px;"><img src="{qr_url}" width="100"></div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                with st.container(border=True):
                    st.subheader("⚡ Quick Actions")
                    ca, cb = st.columns(2)
                    e_ent = ca.toggle("Check In", value=(row['Entry_Status']=='Done'))
                    e_tsh = cb.toggle("Give Kit", value=(row['T_Shirt_Collected']=='Yes'))
                    
                    # 🔥 NEW: DASHBOARD UNASSIGN FEATURE 🔥
                    if row['Bus_Number'] != 'Unassigned':
                        if st.button("❌ UNASSIGN BUS", type="secondary", use_container_width=True):
                            st.session_state.df.at[idx, 'Bus_Number'] = 'Unassigned'
                            conn.update(worksheet="Data", data=st.session_state.df)
                            add_log(f"Unassigned bus for {row['Name']}")
                            st.warning(f"Bus unassigned for {row['Name']}")
                            time.sleep(0.5)
                            st.rerun()
                    
                    if st.button("💾 SAVE CHANGES", type="primary", use_container_width=True):
                        st.session_state.df.at[idx, 'Entry_Status'] = 'Done' if e_ent else 'N/A'
                        if e_ent and row['Entry_Time'] == 'N/A':
                             st.session_state.df.at[idx, 'Entry_Time'] = datetime.now().strftime("%H:%M:%S")
                        
                        sz = row['T_Shirt_Size']
                        if e_tsh and row['T_Shirt_Collected'] != 'Yes':
                            st.session_state.stock[sz] -= 1
                        st.session_state.df.at[idx, 'T_Shirt_Collected'] = 'Yes' if e_tsh else 'No'
                        
                        conn.update(worksheet="Data", data=st.session_state.df)
                        add_log(f"Updated status for {row['Name']}")
                        st.success("Synchronized!")
                        time.sleep(0.5)
                        st.rerun()

                if st.session_state.user_role == 'admin':
                    with st.expander("🛠 Admin Profile Edit"):
                        with st.form("admin_edit"):
                            en = st.text_input("Name", row['Name'])
                            et = st.text_input("Ticket", row['Ticket_Number'])
                            er = st.selectbox("Role", ["Student", "Volunteer", "Teacher", "Organizer"], index=0)
                            eb = st.selectbox("Bus", ["Bus 1", "Bus 2", "Bus 3", "Bus 4", "Unassigned"], index=0)
                            if st.form_submit_button("Force Update"):
                                st.session_state.df.at[idx, 'Name'] = en
                                st.session_state.df.at[idx, 'Ticket_Number'] = et
                                st.session_state.df.at[idx, 'Role'] = er
                                st.session_state.df.at[idx, 'Bus_Number'] = eb
                                conn.update(worksheet="Data", data=st.session_state.df)
                                st.success("Admin Update Successful")
                                st.rerun()
        else: st.warning("No matches in database!")

# --- 6. MODULE: TEACHERS ---
elif menu == "👨‍🏫 Teachers":
    st.title("👨‍🏫 Teacher Management")
    if st.session_state.user_role == 'admin':
        with st.expander("➕ Add New Teacher"):
            with st.form("t_add"):
                tn = st.text_input("Name"); tp = st.text_input("Phone"); tt = st.text_input("Ticket")
                if st.form_submit_button("Add Teacher"):
                    new_t = {'Name': tn, 'Role': 'Teacher', 'Spot Phone': tp, 'Ticket_Number': tt, 'Entry_Status': 'N/A', 'Bus_Number': 'Unassigned'}
                    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_t])], ignore_index=True)
                    conn.update(worksheet="Data", data=st.session_state.df)
                    st.success("Teacher Added!"); st.rerun()
    st.dataframe(st.session_state.df[st.session_state.df['Role'] == 'Teacher'], use_container_width=True)

# --- 7. MODULE: SMART TRANSPORT ---
elif menu == "🚌 Smart Transport":
    st.title("🚌 Fleet Logistics")
    buses = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    cols = st.columns(4)
    for i, b in enumerate(buses):
        count = len(st.session_state.df[st.session_state.df['Bus_Number'] == b])
        cols[i].metric(b, f"{count}/{BUS_CAPACITY}", f"{BUS_CAPACITY-count} Seats Free")
        cols[i].progress(min(count/BUS_CAPACITY, 1.0))

    st.markdown("---")
    with st.expander("🚀 Smart Auto-Assign"):
        c1, c2, c3 = st.columns(3)
        mode = c1.selectbox("Filter", ["Class", "Role"])
        opts = sorted(st.session_state.df[mode].unique())
        val = c2.selectbox("Select Group", opts)
        target_b = c3.selectbox("Starting Bus", buses)
        
        if st.button("Start Sequence"):
            indices = st.session_state.df[st.session_state.df[mode] == val].index.tolist()
            b_idx = buses.index(target_b)
            for p_idx in indices:
                while b_idx < 4:
                    if len(st.session_state.df[st.session_state.df['Bus_Number'] == buses[b_idx]]) < BUS_CAPACITY:
                        st.session_state.df.at[p_idx, 'Bus_Number'] = buses[b_idx]; break
                    else: b_idx += 1
            conn.update(worksheet="Data", data=st.session_state.df)
            st.success("Assigned!"); st.rerun()

# --- 8. MODULE: INVENTORY ---
elif menu == "📦 Inventory":
    st.title("📦 Inventory Control")
    cols = st.columns(5)
    for i, s in enumerate(["S", "M", "L", "XL", "XXL"]):
        cols[i].metric(s, st.session_state.stock.get(s, 0))
    with st.form("inv"):
        sz = st.selectbox("Size", ["S", "M", "L", "XL", "XXL"]); qty = st.number_input("New Quantity", 0)
        if st.form_submit_button("Update"):
            st.session_state.stock[sz] = qty
            data = [{"Size": k, "Quantity": v} for k, v in st.session_state.stock.items()]
            conn.update(worksheet="Stock", data=pd.DataFrame(data))
            st.rerun()

# --- 9. MODULE: ANALYTICS ---
elif menu == "📊 Analytics":
    st.title("📊 Data Insights")
    st.bar_chart(st.session_state.df['Bus_Number'].value_counts())
    st.bar_chart(st.session_state.df['T_Shirt_Size'].value_counts())

# --- 10. MODULE: ADMIN LOGS & EXPORT ---
elif menu == "⚙️ Admin Logs":
    st.title("⚙️ System Logs & Export")
    t1, t2 = st.tabs(["📜 Logs", "📥 Export"])
    with t1:
        for log in st.session_state.logs: st.text(log)
    with t2:
        if st.button("📄 Generate Printable Bus Manifest"):
            html = "<html><head><meta charset='UTF-8'></head><body><h1>Bus Manifest</h1>"
            for b in ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]:
                bdf = st.session_state.df[st.session_state.df['Bus_Number'] == b]
                if not bdf.empty:
                    html += f"<h2>{b}</h2><table border='1' width='100%'><tr><th>Sl.</th><th>Name</th><th>Class</th><th>In Sign</th><th>Out Sign</th></tr>"
                    for j, (_, r) in enumerate(bdf.iterrows(), 1):
                        html += f"<tr><td>{j}</td><td>{r['Name']}</td><td>{r['Class']}</td><td></td><td></td></tr>"
                    html += "</table>"
            st.download_button("Download HTML", html, "Manifest.html", "text/html")
