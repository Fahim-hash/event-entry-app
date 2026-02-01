import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# ==================== 0. PAGE CONFIG & CUSTOM CSS ====================
st.set_page_config(page_title="Event Manager Pro", page_icon="🔥", layout="wide")

st.markdown("""
    <style>
    .stApp {background-color: #0e1117;}
    input[type="text"] {
        border-radius: 10px !important;
        border: 1px solid #3b3f4a !important;
        padding: 10px !important;
    }
    div[data-testid="stMetric"] {
        background-color: #1e2129;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #ff4b4b;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .id-card {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        padding: 20px;
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
    .id-name { font-size: 26px; font-weight: bold; margin: 10px 0; text-shadow: 2px 2px 4px #000; }
    .id-info { font-size: 15px; margin: 5px 0; color: #e0e0e0; }
    .tshirt-badge {
        font-size: 16px; font-weight: bold; margin-top: 15px; padding: 8px; 
        border-radius: 8px; background: rgba(0,0,0,0.4); border: 1px solid #fff;
    }
    .status-badge {
        margin-top: 10px; font-size: 16px; font-weight: bold; padding: 8px; 
        border-radius: 8px; background: rgba(255, 255, 255, 0.1); border: 1px solid #fff;
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

# ==================== 2. DATA ENGINE ====================
BUS_CAPACITY = 45
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Data", ttl=0)
        cols = ['Name', 'Role', 'Spot Phone', 'Guardian Phone', 'Ticket_Number', 'Class', 'Roll', 'Entry_Status', 'Entry_Time', 'Bus_Number', 'T_Shirt_Size', 'T_Shirt_Collected', 'Notes']
        for c in cols:
            if c not in df.columns: df[c] = ''
        
        for col in ['Ticket_Number', 'Spot Phone', 'Guardian Phone', 'Roll']:
            df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().replace('nan', 'N/A')
        
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

menu_opts = ["🏠 Dashboard", "🔍 Search & Manage", "👨‍🏫 Teachers"]
if st.session_state.user_role == 'admin':
    menu_opts += ["📊 Analytics", "📦 Stock", "🚌 Bus Fleet", "📥 Export"]

menu = st.sidebar.radio("Menu:", menu_opts)

# ADD PERSON SHORTCUT
if st.session_state.user_role == 'admin':
    st.sidebar.markdown("---")
    with st.sidebar.expander("➕ Add Person"):
        with st.form("add_fast"):
            n = st.text_input("Name")
            r = st.selectbox("Role", ["Student", "Volunteer", "Organizer", "Teacher", "Guest"])
            t = st.text_input("Ticket (Mandatory)")
            p = st.text_input("Spot Phone (Mandatory)")
            gp = st.text_input("Guardian Phone")
            
            if st.form_submit_button("Add Now"):
                if n and p and t:
                    new = {
                        'Name': n, 'Role': r, 
                        'Spot Phone': str(p), 'Guardian Phone': str(gp), 'Ticket_Number': str(t), 
                        'Class': 'New', 'Roll': '', 'Entry_Status': '', 'Bus_Number': 'Unassigned', 
                        'T_Shirt_Size': 'L', 'T_Shirt_Collected': 'No', 'Notes': 'Added'
                    }
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
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total People", len(df))
    c2.metric("Checked In", len(df[df['Entry_Status']=='Done']))
    c3.metric("T-Shirts Out", len(df[df['T_Shirt_Collected']=='Yes']))
    c4.metric("Pending", len(df[df['Entry_Status']!='Done']))
    st.progress(len(df[df['Entry_Status']=='Done']) / len(df) if len(df) > 0 else 0)
    
    st.subheader("📡 Live Feed")
    recent = df[df['Entry_Status']=='Done'].sort_values('Entry_Time', ascending=False).head(5)
    st.dataframe(recent[['Name', 'Role', 'Entry_Time', 'Bus_Number']], use_container_width=True)

# --- TEACHERS TAB ---
elif menu == "👨‍🏫 Teachers":
    st.title("👨‍🏫 Teacher Management")
    df_t = st.session_state.df[st.session_state.df['Role'] == 'Teacher']
    col1, col2 = st.columns(2)
    col1.metric("Total Teachers", len(df_t))
    col2.metric("Teachers Present", len(df_t[df_t['Entry_Status'] == 'Done']))
    st.markdown("---")
    
    t_list = df_t['Name'].tolist()
    selected_t = st.selectbox("Select Teacher:", ["Select..."] + t_list)
    
    if selected_t != "Select...":
        idx = st.session_state.df[st.session_state.df['Name'] == selected_t].index[0]
        row = st.session_state.df.loc[idx]
        
        c_stat, c_act = st.columns([1, 2])
        with c_stat:
            if row['Entry_Status'] == 'Done': st.success("✅ ALREADY ENTERED")
            else: st.warning("⏳ NOT ENTERED")
            st.info(f"Bus: {row['Bus_Number']}")

        with c_act:
            with st.form("teacher_entry"):
                check_ent = st.checkbox("✅ Mark Entry", value=(row['Entry_Status']=='Done'))
                check_tsh = st.checkbox("👕 T-Shirt Given", value=(row['T_Shirt_Collected']=='Yes'))
                bus_opts = ["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"]
                sel_bus = st.selectbox("Assign Bus", bus_opts, index=bus_opts.index(row['Bus_Number']) if row['Bus_Number'] in bus_opts else 0)
                
                if st.form_submit_button("💾 Update"):
                    st.session_state.df.at[idx, 'Entry_Status'] = 'Done' if check_ent else ''
                    if check_ent and not row['Entry_Time']:
                        st.session_state.df.at[idx, 'Entry_Time'] = datetime.now().strftime("%H:%M:%S")
                    sz = row['T_Shirt_Size']
                    if check_tsh and row['T_Shirt_Collected'] == 'No':
                        st.session_state.stock[sz] -= 1
                        save_stock()
                    elif not check_tsh and row['T_Shirt_Collected'] == 'Yes':
                        st.session_state.stock[sz] += 1
                        save_stock()
                    st.session_state.df.at[idx, 'T_Shirt_Collected'] = 'Yes' if check_tsh else 'No'
                    st.session_state.df.at[idx, 'Bus_Number'] = sel_bus
                    save_data()
                    st.success("Updated!")
                    st.rerun()
    st.dataframe(df_t[['Name', 'Spot Phone', 'Entry_Status', 'Bus_Number', 'T_Shirt_Collected']], use_container_width=True)

# --- SEARCH & MANAGE ---
elif menu == "🔍 Search & Manage":
    st.title("🔍 Search & Digital ID")
    q = st.text_input("🔎 Search by Ticket / Name / Phone:", placeholder="Type anything...").strip()
    
    if q:
        mask = (
            st.session_state.df['Name'].astype(str).str.contains(q, case=False) |
            st.session_state.df['Ticket_Number'].astype(str).str.contains(q, case=False) |
            st.session_state.df['Spot Phone'].astype(str).str.contains(q, case=False) |
            st.session_state.df['Guardian Phone'].astype(str).str.contains(q, case=False) |
            st.session_state.df['Roll'].astype(str).str.contains(q, case=False)
        )
        res = st.session_state.df[mask]
        
        if not res.empty:
            idx = res.index[0]
            if len(res) > 1:
                st.info(f"Found {len(res)} matches!")
                sel = st.selectbox("Select Person:", res['Name'].tolist())
                idx = res[res['Name'] == sel].index[0]
            
            row = st.session_state.df.loc[idx]
            
            # CARD LOGIC
            sz = row['T_Shirt_Size']
            rem_stock = st.session_state.stock.get(sz, 0)
            if row['T_Shirt_Collected'] == 'Yes':
                t_status, t_color = f"👕 {sz} : GIVEN ✅", "#4ade80"
            elif rem_stock > 0:
                t_status, t_color = f"👕 {sz} : IN STOCK ({rem_stock}) 📦", "#60a5fa"
            else:
                t_status, t_color = f"👕 {sz} : OUT OF STOCK ❌", "#f87171"

            col_card, col_action = st.columns([1, 1.5])
            with col_card:
                st.markdown(f"""
<div class="id-card">
<div class="id-role">{row['Role'].upper()}</div>
<div class="id-name">{row['Name']}</div>
<div class="id-info">🎟 Ticket: <b>{row['Ticket_Number']}</b></div>
<div class="id-info">🆔 Roll: {row['Roll']}</div>
<div class="id-info">📞 Spot: {row['Spot Phone']}</div>
<div class="id-info">👨‍👩‍👦 G. Phone: {row['Guardian Phone']}</div>
<div class="id-info">🚌 Bus: {row['Bus_Number']}</div>
<div class="tshirt-badge" style="color: {t_color}; border: 1px solid {t_color};">{t_status}</div>
<div class="status-badge" style="color: {'#4ade80' if row['Entry_Status']=='Done' else '#f87171'}; border: 1px solid {'#4ade80' if row['Entry_Status']=='Done' else '#f87171'};">{'✅ CHECKED IN' if row['Entry_Status']=='Done' else '⏳ NOT ENTERED'}</div>
</div>
""", unsafe_allow_html=True)

            with col_action:
                with st.container(border=True):
                    st.subheader("⚡ Quick Actions")
                    c1, c2 = st.columns(2)
                    new_ent = c1.checkbox("✅ Mark Entry", value=(row['Entry_Status']=='Done'), key="ent")
                    new_tsh = c2.checkbox("👕 T-Shirt Given", value=(row['T_Shirt_Collected']=='Yes'), key="tsh")
                    
                    if st.button("💾 Save Status", type="primary"):
                        st.session_state.df.at[idx, 'Entry_Status'] = 'Done' if new_ent else ''
                        if new_ent and not row['Entry_Time']:
                            st.session_state.df.at[idx, 'Entry_Time'] = datetime.now().strftime("%H:%M:%S")
                        
                        if new_tsh and row['T_Shirt_Collected'] == 'No':
                            st.session_state.stock[sz] -= 1
                            save_stock()
                        elif not new_tsh and row['T_Shirt_Collected'] == 'Yes':
                            st.session_state.stock[sz] += 1
                            save_stock()
                        st.session_state.df.at[idx, 'T_Shirt_Collected'] = 'Yes' if new_tsh else 'No'
                        save_data()
                        st.success("Updated!")
                        st.rerun()

                if st.session_state.user_role == 'admin':
                    with st.expander("📝 Edit Full Profile"):
                        with st.form("super_edit"):
                            c_a, c_b = st.columns(2)
                            e_name = c_a.text_input("Name", row['Name'])
                            e_phone = c_b.text_input("Spot Phone", row['Spot Phone'])
                            c_c, c_d = st.columns(2)
                            e_gp = c_c.text_input("Guardian Phone", row['Guardian Phone'])
                            e_tick = c_d.text_input("Ticket No", row['Ticket_Number'])
                            c_e, c_f = st.columns(2)
                            e_roll = c_e.text_input("Roll", row['Roll'])
                            roles = ["Student", "Volunteer", "Organizer", "Teacher", "Guest"]
                            e_role = c_f.selectbox("Role", roles, index=roles.index(row['Role']) if row['Role'] in roles else 0)
                            c_g, c_h = st.columns(2)
                            buses = ["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"]
                            e_bus = c_g.selectbox("Bus", buses, index=buses.index(row['Bus_Number']) if row['Bus_Number'] in buses else 0)
                            e_size = c_h.selectbox("Size", ["S", "M", "L", "XL", "XXL"], index=["S", "M", "L", "XL", "XXL"].index(row['T_Shirt_Size']))
                            
                            if st.form_submit_button("💾 Save Changes"):
                                st.session_state.df.at[idx, 'Name'] = e_name
                                st.session_state.df.at[idx, 'Spot Phone'] = str(e_phone)
                                st.session_state.df.at[idx, 'Guardian Phone'] = str(e_gp)
                                st.session_state.df.at[idx, 'Ticket_Number'] = str(e_tick)
                                st.session_state.df.at[idx, 'Roll'] = str(e_roll)
                                st.session_state.df.at[idx, 'Role'] = e_role
                                st.session_state.df.at[idx, 'Bus_Number'] = e_bus
                                st.session_state.df.at[idx, 'T_Shirt_Size'] = e_size
                                save_data()
                                st.success("Updated!")
                                st.rerun()
        else: st.warning("No matches found!")

# --- ANALYTICS ---
elif menu == "📊 Analytics":
    st.title("📊 Analytics")
    t1, t2 = st.tabs(["🚌 Transport", "👕 Merchandise"])
    with t1: st.bar_chart(st.session_state.df['Bus_Number'].value_counts())
    with t2: st.bar_chart(st.session_state.df['T_Shirt_Size'].value_counts())

# --- STOCK ---
elif menu == "📦 Stock":
    st.title("📦 Inventory")
    cols = st.columns(5)
    for s in ["S", "M", "L", "XL", "XXL"]:
        cols[cols.index(cols[0])+["S", "M", "L", "XL", "XXL"].index(s)].metric(s, st.session_state.stock.get(s, 0))
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
    st.title("🚌 Smart Fleet Manager")
    cols = st.columns(4)
    bus_names = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    for i, b in enumerate(bus_names):
        count = len(st.session_state.df[st.session_state.df['Bus_Number'] == b])
        cols[i].metric(b, f"{count}/{BUS_CAPACITY}", delta=f"{BUS_CAPACITY-count} left", delta_color="normal")
    
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    grp = c1.selectbox("Role Group", ["Student", "Volunteer", "Teacher"])
    start_bus_idx = c2.selectbox("Start Bus", bus_names)
    
    if c3.button("🚀 Smart Assign", type="primary"):
        mask = st.session_state.df['Role'] == grp
        people_indices = st.session_state.df[mask].index.tolist()
        curr_bus_idx = bus_names.index(start_bus_idx)
        for pid in people_indices:
            curr_bus_name = bus_names[curr_bus_idx]
            curr_count = len(st.session_state.df[st.session_state.df['Bus_Number'] == curr_bus_name])
            if curr_count < BUS_CAPACITY:
                st.session_state.df.at[pid, 'Bus_Number'] = curr_bus_name
            else:
                if curr_bus_idx < 3: curr_bus_idx += 1
                else: break
        save_data()
        st.success("Smart Assigned!")
        st.rerun()

    if c4.button("❌ Unassign"):
        mask = st.session_state.df['Role'] == grp
        st.session_state.df.loc[mask, 'Bus_Number'] = 'Unassigned'
        save_data()
        st.warning("Unassigned!")
        st.rerun()

    tabs = st.tabs(["Unassigned"] + bus_names)
    with tabs[0]: st.dataframe(st.session_state.df[st.session_state.df['Bus_Number'].isin(['Unassigned', ''])][['Name', 'Role', 'Class']])
    for i, b in enumerate(bus_names):
        with tabs[i+1]: st.dataframe(st.session_state.df[st.session_state.df['Bus_Number'] == b][['Name', 'Role']])

# --- EXPORT ---
elif menu == "📥 Export":
    st.title("📥 Export Data")
    
    st.markdown("### 📄 Printable Bus Lists")
    
    # HTML GENERATION Logic
    html_content = """
    <html>
    <head>
    <style>
        body { font-family: Arial, sans-serif; }
        .bus-title { font-size: 30px; font-weight: bold; text-align: center; margin-top: 20px; text-transform: uppercase; border-bottom: 3px solid #000; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #000; padding: 10px; text-align: left; font-size: 14px; }
        th { background-color: #f2f2f2; }
        .page-break { page-break-before: always; }
        .sign-col { width: 150px; }
    </style>
    </head>
    <body>
    """
    
    bus_list = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    has_data = False
    
    for bus in bus_list:
        # Filter data for this bus
        bus_df = st.session_state.df[st.session_state.df['Bus_Number'] == bus].copy()
        
        if not bus_df.empty:
            has_data = True
            # Add Page Break for buses after the first one
            if bus != "Bus 1":
                html_content += '<div class="page-break"></div>'
            
            html_content += f'<div class="bus-title">{bus} Manifest</div>'
            html_content += f'<p>Total Passengers: {len(bus_df)}</p>'
            html_content += '<table><thead><tr><th>Sl.</th><th>Class</th><th>Name</th><th>Ticket No.</th><th class="sign-col">Signature</th></tr></thead><tbody>'
            
            for i, (_, row) in enumerate(bus_df.iterrows(), 1):
                html_content += f"<tr><td>{i}</td><td>{row['Role']}</td><td>{row['Name']}</td><td>{row['Ticket_Number']}</td><td></td></tr>"
            
            html_content += '</tbody></table>'
    
    html_content += "</body></html>"
    
    c1, c2 = st.columns(2)
    
    # Button 1: Printable HTML
    with c1:
        st.download_button(
            label="📄 Download Printable Bus Manifest (PDF Ready)",
            data=html_content,
            file_name="Bus_Manifest_Printable.html",
            mime="text/html",
            help="Download this file and open in Chrome/Edge. Then press Ctrl+P to save as PDF or Print."
        )
    
    # Button 2: Raw CSV
    with c2:
        st.download_button(
            label="💾 Download Full Database (CSV)",
            data=st.session_state.df.to_csv(index=False).encode('utf-8'),
            file_name=f"Event_Data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
