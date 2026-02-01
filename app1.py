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
BUS_CAPACITY = 45
STUDENT_LIMIT = 43  # 43 Students + 1 Org + 1 Teacher = 45

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
                        # Validation
                        if not new_phone or new_phone == 'N/A' or not new_ticket or new_ticket == 'N/A':
                            st.error("❌ Phone & Ticket are REQUIRED!")
                        else:
                            # Bus Limit Check
                            can_assign = True
                            if new_bus != "Unassigned":
                                bus_pax = df[df['Bus_Number'] == new_bus]
                                bus_pax = bus_pax[bus_pax.index != idx]
                                total_in_bus = len(bus_pax)
                                student_in_bus = len(bus_pax[bus_pax['Role'] == 'Student'])
                                
                                if new_role == "Student":
                                    if student_in_bus >= STUDENT_LIMIT:
                                        st.error(f"⛔ {new_bus} Student Limit Reached (43/45)! Seats Reserved.")
                                        can_assign = False
                                    elif total_in_bus >= BUS_CAPACITY:
                                        st.error(f"⛔ {new_bus} is FULL!")
                                        can_assign = False
                                else: # Teachers/Staff
                                    if total_in_bus >= BUS_CAPACITY:
                                        st.error(f"⛔ {new_bus} is FULL!")
                                        can_assign = False

                            if can_assign:
                                # Stock Update
                                if new_kit:
                                    if is_kit and sz != new_size:
                                        st.session_state.stock[sz] += 1
                                        st.session_state.stock[new_size] -= 1
                                    elif not is_kit:
                                        st.session_state.stock[new_size] -= 1
                                elif not new_kit and is_kit:
                                    st.session_state.stock[sz] += 1
                                
                                # Data Save
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
                                st.success("✅ Updated Successfully!")
                                time.sleep(0.5); st.rerun()
        else: st.warning("No user found!")

# --- TAB 2: ADD STAFF/TEACHER (NEW FEATURE) ---
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
        if is_class_teacher:
            class_name = st.text_input("Assigned Class Name (e.g., Class 10 - Science)")
        
        if st.form_submit_button("➕ Add to Database"):
            if name and phone:
                # Create Manual ID
                manual_ticket = f"MAN-{int(time.time())}"
                
                new_entry = {
                    'Name': name,
                    'Role': role,
                    'Spot Phone': phone,
                    'Guardian Phone': 'N/A',
                    'Ticket_Number': manual_ticket,
                    'Class': class_name,
                    'Roll': 'N/A',
                    'Entry_Status': 'N/A',
                    'Entry_Time': 'N/A',
                    'Bus_Number': 'Unassigned',
                    'T_Shirt_Size': 'L', # Default
                    'T_Shirt_Collected': 'No',
                    'Notes': 'Manual Entry'
                }
                
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_entry])], ignore_index=True)
                conn.update(worksheet="Data", data=st.session_state.df)
                st.success(f"✅ {name} ({role}) added successfully!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Name and Phone are required!")

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
        stus = len(df_b[df_b['Role'] == 'Student'])
        cols[i].metric(b, f"{cnt}/45", f"Students: {stus}/43")
        cols[i].progress(min(cnt/45, 1.0))
    
    st.markdown("---")
    st.subheader("📋 Bus Passenger List")
    sel_bus = st.selectbox("Select Bus:", buses)
    b_df = st.session_state.df[st.session_state.df['Bus_Number'] == sel_bus]
    if not b_df.empty:
        st.dataframe(b_df[['Name', 'Role', 'Class', 'Spot Phone']], use_container_width=True)
    else: st.info("Bus Empty")
    
    st.markdown("---")
    st.subheader("🚀 Smart Auto-Assign")
    c1, c2, c3 = st.columns(3)
    role = c1.selectbox("Role", ["Student", "Volunteer", "Teacher"])
    start_b = c2.selectbox("Start Bus", buses)
    
    if c3.button("Auto Assign"):
        mask = st.session_state.df['Role'] == role
        indices = st.session_state.df[mask].index.tolist()
        b_idx = buses.index(start_b)
        assigned_cnt = 0
        for pid in indices:
            while b_idx < 4:
                curr_bus = buses[b_idx]
                curr_df = st.session_state.df[st.session_state.df['Bus_Number'] == curr_bus]
                total_load = len(curr_df)
                stu_load = len(curr_df[curr_df['Role'] == 'Student'])
                
                can_fit = False
                if role == "Student":
                    if stu_load < STUDENT_LIMIT: can_fit = True
                else:
                    if total_load < BUS_CAPACITY: can_fit = True
                
                if can_fit:
                    st.session_state.df.at[pid, 'Bus_Number'] = curr_bus
                    assigned_cnt += 1
                    break
                else: b_idx += 1
        conn.update(worksheet="Data", data=st.session_state.df)
        st.success(f"Assigned {assigned_cnt} people!")
        st.rerun()

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
