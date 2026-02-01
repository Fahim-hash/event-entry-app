import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time
import altair as alt

# ==================== 1. CONFIG & STYLE ====================
st.set_page_config(page_title="Event OS Pro", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #e0e0e0; }
    
    /* Stats Box */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px; padding: 10px;
    }
    
    /* ID Card Design */
    .id-card {
        background: linear-gradient(135deg, #121212 0%, #1e1e1e 100%);
        border: 2px solid #333; border-radius: 15px; padding: 20px;
        text-align: center; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .id-name { font-size: 26px; font-weight: bold; margin: 10px 0; color: white; }
    .role-badge { background: #FFD700; color: black; padding: 2px 10px; border-radius: 10px; font-weight: bold; font-size: 12px; }
    
    /* Input Fields Style */
    input[type="text"] {
        border: 1px solid #444 !important; background-color: #1a1a1a !important; color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== 2. DATA ENGINE ====================
conn = st.connection("gsheets", type=GSheetsConnection)

# Constants
BUS_CAPACITY = 45  # Hard Limit

def load_data():
    try:
        df = conn.read(worksheet="Data", ttl=0)
        req_cols = ['Name', 'Role', 'Spot Phone', 'Guardian Phone', 'Ticket_Number', 'Class', 'Roll', 'Entry_Status', 'Entry_Time', 'Bus_Number', 'T_Shirt_Size', 'T_Shirt_Collected', 'Notes']
        for c in req_cols:
            if c not in df.columns: df[c] = ''
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

# ==================== 3. SIMPLE LOGIN ====================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Admin Login")
    c1, c2 = st.columns(2)
    with c1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login", type="primary"):
            if u == "admin" and p == "1234":
                st.session_state.logged_in = True
                st.session_state.user = u
                st.rerun()
            else: st.error("Wrong Password!")
    st.stop()

# ==================== 4. MAIN APP LAYOUT ====================
st.sidebar.title("⚡ Menu")
menu = st.sidebar.radio("Go To", ["🔍 Search & Entry", "➕ Add Staff/Teacher", "📜 Class Lists", "🚌 Bus Manager", "📊 Dashboard", "📝 Admin Data"])

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.session_state.df = load_data()
    st.session_state.stock = load_stock()
    st.rerun()

# --- TAB 1: SEARCH & ENTRY ---
if menu == "🔍 Search & Entry":
    st.title("🔍 Search, Edit & Entry")
    
    q = st.text_input("🔎 Search by Ticket / Name / Phone:", placeholder="Type here...").strip()
    
    if q:
        df = st.session_state.df
        mask = df['Name'].str.contains(q, case=False) | df['Ticket_Number'].str.contains(q, case=False) | df['Spot Phone'].str.contains(q, case=False)
        res = df[mask]
        
        if not res.empty:
            idx = res.index[0]
            row = df.loc[idx]
            
            # Variables
            is_ent = row['Entry_Status'] == 'Done'
            is_kit = row['T_Shirt_Collected'] == 'Yes'
            sz = row['T_Shirt_Size']
            rem = st.session_state.stock.get(sz, 0)
            
            # Stock Warning
            if not is_kit:
                if rem == 0: st.error(f"❌ OUT OF STOCK! No {sz} size available.")
                elif rem <= 5: st.warning(f"⚠️ LOW STOCK ALERT: Only {rem} remaining!")

            col1, col2 = st.columns([1, 1.5])
            
            with col1:
                border_c = "#00ff88" if is_ent else "#ff4b4b"
                st.markdown(f"""
                <div class="id-card" style="border: 2px solid {border_c};">
                    <div style="background:{border_c}; color:black; font-weight:bold; padding:5px; border-radius:5px;">
                        {'✅ CHECKED IN' if is_ent else '⏳ NOT ENTERED'}
                    </div>
                    <br><span class="role-badge">{row['Role']}</span>
                    <div class="id-name">{row['Name']}</div>
                    <div class="info-row"><span>Ticket:</span> <b>{row['Ticket_Number']}</b></div>
                    <div class="info-row"><span>Bus:</span> <b>{row['Bus_Number']}</b></div>
                    <div style="margin-top:10px; border:1px solid #555; padding:8px; border-radius:8px;">
                        👕 Size: <b>{sz}</b> | Status: {'✅ GIVEN' if is_kit else f'📦 {rem} Left'}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Single Unassign
                if row['Bus_Number'] != "Unassigned":
                    if st.button(f"❌ Unassign from {row['Bus_Number']}", type="secondary", use_container_width=True):
                        st.session_state.df.at[idx, 'Bus_Number'] = 'Unassigned'
                        conn.update(worksheet="Data", data=st.session_state.df)
                        st.success(f"Removed from {row['Bus_Number']}!"); time.sleep(0.5); st.rerun()

            with col2:
                with st.container(border=True):
                    st.subheader("✏️ Edit Information")
                    c_name, c_role = st.columns([1.5, 1])
                    new_name = c_name.text_input("Name", value=row['Name'])
                    role_opts = ["Student", "Volunteer", "Teacher", "College Staff", "Organizer"]
                    new_role = c_role.selectbox("Role", role_opts, index=role_opts.index(row['Role']) if row['Role'] in role_opts else 0)
                    
                    c_ph, c_tk = st.columns(2)
                    new_phone = c_ph.text_input("Phone (Req)", value=row['Spot Phone'])
                    new_ticket = c_tk.text_input("Ticket (Req)", value=row['Ticket_Number'])
                    
                    sz_list = ["S", "M", "L", "XL", "XXL"]
                    new_size = st.selectbox("Update Size", sz_list, index=sz_list.index(sz) if sz in sz_list else 2)
                    
                    st.markdown("---")
                    st.subheader("⚡ Actions")
                    c_a, c_b = st.columns(2)
                    new_ent = c_a.toggle("✅ Mark Entry", value=is_ent)
                    new_kit = c_b.toggle("👕 Give T-Shirt", value=is_kit)
                    
                    buses = ["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"]
                    new_bus = st.selectbox("🚌 Assign Bus", buses, index=buses.index(row['Bus_Number']) if row['Bus_Number'] in buses else 0)
                    
                    if st.button("💾 Save Changes", type="primary", use_container_width=True):
                        if not new_phone or new_phone == 'N/A' or not new_ticket or new_ticket == 'N/A':
                            st.error("❌ Phone & Ticket are REQUIRED!")
                        else:
                            can_assign = True
                            if new_bus != "Unassigned" and new_bus != row['Bus_Number']:
                                bus_pax = df[df['Bus_Number'] == new_bus]
                                if len(bus_pax) >= BUS_CAPACITY:
                                    st.error(f"⛔ {new_bus} is FULL ({len(bus_pax)}/{BUS_CAPACITY})!"); can_assign = False

                            if can_assign:
                                if new_kit:
                                    if is_kit and sz != new_size:
                                        st.session_state.stock[sz] += 1
                                        st.session_state.stock[new_size] -= 1
                                    elif not is_kit:
                                        st.session_state.stock[new_size] -= 1
                                elif not new_kit and is_kit:
                                    st.session_state.stock[sz] += 1
                                
                                st.session_state.df.at[idx, 'Name'] = new_name
                                st.session_state.df.at[idx, 'Role'] = new_role
                                st.session_state.df.at[idx, 'Spot Phone'] = new_phone
                                st.session_state.df.at[idx, 'Ticket_Number'] = new_ticket
                                st.session_state.df.at[idx, 'T_Shirt_Size'] = new_size
                                st.session_state.df.at[idx, 'Entry_Status'] = 'Done' if new_ent else 'N/A'
                                st.session_state.df.at[idx, 'T_Shirt_Collected'] = 'Yes' if new_kit else 'No'
                                st.session_state.df.at[idx, 'Bus_Number'] = new_bus
                                
                                if new_ent and row['Entry_Time'] == 'N/A':
                                    st.session_state.df.at[idx, 'Entry_Time'] = datetime.now().strftime("%H:%M:%S")
                                
                                conn.update(worksheet="Data", data=st.session_state.df)
                                s_d = [{"Size": k, "Quantity": v} for k, v in st.session_state.stock.items()]
                                conn.update(worksheet="Stock", data=pd.DataFrame(s_d))
                                st.success("✅ Updated!"); time.sleep(0.5); st.rerun()
        else: st.warning("No user found!")

# --- TAB 2: ADD STAFF/TEACHER ---
elif menu == "➕ Add Staff/Teacher":
    st.title("➕ Manually Add Teacher or Staff")
    with st.form("add_staff_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Full Name")
        phone = c2.text_input("Phone Number")
        c3, c4 = st.columns(2)
        role = c3.selectbox("Role", ["Teacher", "College Staff", "Guest"])
        is_class_teacher = c4.checkbox("Is Class Teacher?")
        class_name = "N/A"
        if is_class_teacher: class_name = st.text_input("Class Name")
        if st.form_submit_button("➕ Add"):
            if name and phone:
                manual_ticket = f"MAN-{int(time.time())}"
                new_entry = {
                    'Name': name, 'Role': role, 'Spot Phone': phone, 'Guardian Phone': 'N/A',
                    'Ticket_Number': manual_ticket, 'Class': class_name, 'Roll': 'N/A',
                    'Entry_Status': 'N/A', 'Entry_Time': 'N/A', 'Bus_Number': 'Unassigned',
                    'T_Shirt_Size': 'L', 'T_Shirt_Collected': 'No', 'Notes': 'Manual Entry'
                }
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_entry])], ignore_index=True)
                conn.update(worksheet="Data", data=st.session_state.df)
                st.success(f"✅ {name} added!"); time.sleep(1); st.rerun()
            else: st.error("Name & Phone Required!")

# --- TAB 3: CLASS LISTS ---
elif menu == "📜 Class Lists":
    st.title("📜 Class Wise List")
    classes = sorted([c for c in st.session_state.df['Class'].unique() if c not in ['', 'N/A']])
    sel_cls = st.selectbox("Select Class:", ["All"] + classes)
    v_df = st.session_state.df if sel_cls == "All" else st.session_state.df[st.session_state.df['Class'] == sel_cls]
    c1, c2, c3 = st.columns(3)
    c1.metric("Total", len(v_df))
    c2.metric("In", len(v_df[v_df['Entry_Status']=='Done']))
    c3.metric("Pending", len(v_df)-len(v_df[v_df['Entry_Status']=='Done']))
    st.dataframe(v_df[['Name', 'Class', 'Roll', 'Spot Phone', 'Entry_Status']], use_container_width=True)

# --- TAB 4: BUS MANAGER ---
elif menu == "🚌 Bus Manager":
    st.title("🚌 Fleet Management")
    
    buses = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    cols = st.columns(4)
    for i, b in enumerate(buses):
        df_b = st.session_state.df[st.session_state.df['Bus_Number'] == b]
        cnt = len(df_b)
        cols[i].metric(b, f"{cnt}/{BUS_CAPACITY}", f"{BUS_CAPACITY-cnt} Free")
        cols[i].progress(min(cnt/BUS_CAPACITY, 1.0))
    
    # Bulk Unassign
    st.markdown("---")
    with st.expander("🗑️ Mass Unassign Tools"):
        b_c1, b_c2 = st.columns(2)
        with b_c1:
            st.subheader("Empty Bus")
            target_bus = st.selectbox("Select Bus:", buses)
            if st.button(f"🗑️ Empty {target_bus}"):
                mask = st.session_state.df['Bus_Number'] == target_bus
                if mask.sum() > 0:
                    st.session_state.df.loc[mask, 'Bus_Number'] = 'Unassigned'
                    conn.update(worksheet="Data", data=st.session_state.df)
                    st.success("Done!"); time.sleep(1); st.rerun()
        with b_c2:
            st.subheader("Unassign Group")
            grp = st.selectbox("Class to Unassign:", sorted([x for x in st.session_state.df['Class'].unique() if x not in ['']]))
            if st.button(f"❌ Unassign All {grp}"):
                mask = (st.session_state.df['Class'] == grp) & (st.session_state.df['Bus_Number'] != 'Unassigned')
                if mask.sum() > 0:
                    st.session_state.df.loc[mask, 'Bus_Number'] = 'Unassigned'
                    conn.update(worksheet="Data", data=st.session_state.df)
                    st.success("Done!"); time.sleep(1); st.rerun()
    
    # 🔥 A4 PRINT MANIFEST SECTION 🔥
    st.markdown("---")
    st.subheader("🖨️ A4 Print Manifest")
    
    p_bus = st.selectbox("Select Bus to Print:", ["All Buses"] + buses)
    
    if st.button("📄 Generate A4 PDF Ready File"):
        html_content = """
        <html>
        <head>
            <style>
                @page { size: A4; margin: 10mm; }
                body { font-family: 'Arial', sans-serif; font-size: 12px; }
                .bus-page { page-break-after: always; width: 100%; }
                h1 { text-align: center; font-size: 18px; text-decoration: underline; margin-bottom: 5px; }
                .meta { text-align: center; margin-bottom: 20px; font-size: 14px; }
                table { width: 100%; border-collapse: collapse; }
                th, td { border: 1px solid black; padding: 6px; text-align: left; }
                th { background-color: #f0f0f0; font-weight: bold; }
            </style>
        </head>
        <body>
        """
        
        target_buses = buses if p_bus == "All Buses" else [p_bus]
        
        for bus in target_buses:
            b_df = st.session_state.df[st.session_state.df['Bus_Number'] == bus]
            if not b_df.empty:
                html_content += f"""
                <div class="bus-page">
                    <h1>{bus} Passenger Manifest</h1>
                    <div class="meta">
                        <b>Total Pax:</b> {len(b_df)} &nbsp;|&nbsp; 
                        <b>Date:</b> {datetime.now().strftime('%d-%b-%Y')} &nbsp;|&nbsp; 
                        <b>Supervisor Sign:</b> ___________________
                    </div>
                    <table>
                        <tr>
                            <th style="width:5%">SL</th>
                            <th style="width:30%">Name</th>
                            <th style="width:15%">Role</th>
                            <th style="width:15%">Phone</th>
                            <th style="width:15%">Sign (IN)</th>
                            <th style="width:15%">Sign (OUT)</th>
                        </tr>
                """
                for i, (_, r) in enumerate(b_df.iterrows(), 1):
                    html_content += f"""
                        <tr>
                            <td>{i}</td>
                            <td>{r['Name']}</td>
                            <td>{r['Role']}</td>
                            <td>{r['Spot Phone']}</td>
                            <td></td>
                            <td></td>
                        </tr>
                    """
                html_content += "</table></div>"
        
        html_content += "</body></html>"
        
        st.download_button(
            label="⬇️ Download A4 Print File",
            data=html_content,
            file_name=f"A4_Manifest_{p_bus}_{int(time.time())}.html",
            mime="text/html"
        )
    
    st.markdown("---")
    st.subheader("🚀 Smart Auto-Assign")
    c1, c2, c3 = st.columns(3)
    role = c1.selectbox("Role", ["Student", "Volunteer", "Teacher"])
    start_b = c2.selectbox("Start Bus", buses)
    if c3.button("Auto Assign"):
        mask = st.session_state.df['Role'] == role
        indices = st.session_state.df[mask].index.tolist()
        b_idx = buses.index(start_b)
        cnt = 0
        for pid in indices:
            while b_idx < 4:
                curr = buses[b_idx]
                if len(st.session_state.df[st.session_state.df['Bus_Number'] == curr]) < BUS_CAPACITY:
                    st.session_state.df.at[pid, 'Bus_Number'] = curr
                    cnt += 1; break
                else: b_idx += 1 
        conn.update(worksheet="Data", data=st.session_state.df)
        st.success(f"Assigned {cnt}!"); st.rerun()

# --- TAB 5: DASHBOARD ---
elif menu == "📊 Dashboard":
    st.title("📊 Event Stats")
    df = st.session_state.df
    c1, c2, c3 = st.columns(3)
    c1.metric("Total", len(df))
    c2.metric("Entry", len(df[df['Entry_Status']=='Done']))
    c3.metric("Kits", len(df[df['T_Shirt_Collected']=='Yes']))
    st.bar_chart(df['T_Shirt_Size'].value_counts())

# --- TAB 6: ADMIN DATA ---
elif menu == "📝 Admin Data":
    st.title("📝 Full Database")
    st.dataframe(st.session_state.df)
    if st.button("📥 CSV"):
        st.download_button("Download", st.session_state.df.to_csv(), "data.csv")
