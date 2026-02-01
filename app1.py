import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# ==================== 0. PAGE CONFIG & CUSTOM CSS ====================
st.set_page_config(page_title="Event Manager Pro", page_icon="🎓", layout="wide")

# Custom CSS for Better UI
st.markdown("""
    <style>
    /* Main Background */
    .stApp {background-color: #0e1117;}
    
    /* Metrics Card Styling */
    div[data-testid="stMetric"] {
        background-color: #262730;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #41444d;
        text-align: center;
    }
    
    /* ID Card Styling */
    .id-card {
        background: linear-gradient(135deg, #1f4037, #99f2c8);
        padding: 20px;
        border-radius: 15px;
        color: #000;
        text-align: center;
        font-family: 'Arial', sans-serif;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        margin-bottom: 20px;
    }
    .id-role {
        background-color: #000;
        color: #fff;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
        display: inline-block;
        margin-bottom: 10px;
    }
    .id-name { font-size: 24px; font-weight: bold; margin: 10px 0; }
    .id-details { font-size: 16px; margin: 5px 0; }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #1a1c24;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== 1. LOGIN SYSTEM ====================
USERS = {
    "admin": {"password": "1234", "role": "admin", "name": "Admin Panel"},
    "gate": {"password": "entry26", "role": "volunteer", "name": "Volunteer"}
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
        st.success("Login Successful!")
        st.rerun()
    else:
        st.error("❌ Invalid Credentials")

if not st.session_state.logged_in:
    st.title("🔐 Event Manager Pro")
    c1, c2 = st.columns([1, 2])
    with c1:
        # Just a placeholder image or you can use your logo
        st.markdown("### 🔐 Access")
    with c2:
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("🚀 Login System", on_click=check_login, use_container_width=True)
    st.stop()

# ==================== 2. DATA CONNECTION ====================
BUS_CAPACITY = 45
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Data", ttl=0)
        cols = ['Name', 'Role', 'Spot Phone', 'Ticket_Number', 'Class', 'Roll', 'Entry_Status', 'Entry_Time', 'Bus_Number', 'T_Shirt_Size', 'T_Shirt_Collected', 'Notes']
        for c in cols:
            if c not in df.columns: df[c] = ''
        
        df['Ticket_Number'] = df['Ticket_Number'].astype(str)
        df['Spot Phone'] = df['Spot Phone'].astype(str)
        df['Roll'] = df['Roll'].astype(str)
        return df.fillna('')
    except: return pd.DataFrame(columns=['Name', 'Role', 'Class', 'Ticket_Number'])

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
    except: st.error("Save Error")

def save_stock():
    try:
        data = [{"Size": k, "Quantity": v} for k, v in st.session_state.stock.items()]
        conn.update(worksheet="Stock", data=pd.DataFrame(data))
    except: st.error("Stock Error")

# ==================== 3. UI LAYOUT ====================

# SIDEBAR
st.sidebar.title(f"👋 {st.session_state.user_name}")
if st.sidebar.button("🔄 Refresh System"):
    st.session_state.df = load_data()
    st.session_state.stock = load_stock()
    st.rerun()

menu_opts = ["🏠 Dashboard", "🔍 Search & ID", "📊 Analytics"]
if st.session_state.user_role == 'admin':
    menu_opts += ["👕 Stock Manager", "🚌 Bus Manager", "📥 Export Data"]

menu = st.sidebar.radio("Navigate:", menu_opts)
st.sidebar.markdown("---")
if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 1. DASHBOARD ---
if menu == "🏠 Dashboard":
    st.title("🚀 Event Overview")
    
    df = st.session_state.df
    total = len(df)
    entered = len(df[df['Entry_Status'] == 'Done'])
    pending = total - entered
    
    # Modern Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Total Attendees", total)
    col2.metric("✅ Checked In", entered, delta=f"{int((entered/total)*100) if total else 0}%")
    col3.metric("⏳ Pending", pending, delta_color="inverse")
    col4.metric("🚌 Buses Full", len(df[df['Bus_Number']!='Unassigned']))
    
    st.progress(entered/total if total > 0 else 0)
    
    # Quick View
    st.subheader("📢 Recent Entries")
    st.dataframe(df[df['Entry_Status']=='Done'].sort_values('Entry_Time', ascending=False).head(5)[['Name', 'Entry_Time', 'Bus_Number']], use_container_width=True)

# --- 2. SEARCH & ID CARD ---
elif menu == "🔍 Search & ID":
    st.title("🔍 Search & Digital ID")
    
    col_s1, col_s2 = st.columns([3, 1])
    query = col_s1.text_input("Enter Ticket No / Name / Phone:", placeholder="🔍 Search...")
    
    if query:
        res = st.session_state.df[
            st.session_state.df['Name'].astype(str).str.contains(query, case=False) | 
            st.session_state.df['Ticket_Number'].astype(str).str.contains(query, case=False) |
            st.session_state.df['Spot Phone'].astype(str).str.contains(query, case=False)
        ]
        
        if not res.empty:
            idx = res.index[0]
            if len(res) > 1:
                sel = st.selectbox("Select Person:", res['Name'].tolist())
                idx = res[res['Name'] == sel].index[0]
            
            row = st.session_state.df.loc[idx]
            
            # --- DIGITAL ID CARD DISPLAY ---
            st.markdown(f"""
            <div class="id-card">
                <div class="id-role">{str(row['Role']).upper()}</div>
                <div class="id-name">{row['Name']}</div>
                <div class="id-details">🎟 Ticket: <b>{row['Ticket_Number']}</b></div>
                <div class="id-details">📞 {row['Spot Phone']}</div>
                <div class="id-details">🚌 Bus: {row['Bus_Number']}</div>
                <div style="margin-top:15px; font-size:20px;">
                    {'✅ CHECKED IN' if row['Entry_Status']=='Done' else '⏳ NOT ENTERED'}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # --- ACTIONS ---
            with st.container(border=True):
                st.subheader("⚡ Quick Actions")
                c1, c2, c3 = st.columns(3)
                
                # Checkbox States (Fixed Indentation Here)
                is_entered = c1.checkbox("✅ Mark Entry", value=(row['Entry_Status']=='Done'))
                is_given = c2.checkbox("👕 T-Shirt Given", value=(row['T_Shirt_Collected']=='Yes'))
                
                # Update Button
                if st.button("💾 Update Status", type="primary", use_container_width=True):
                    # Logic
                    st.session_state.df.at[idx, 'Entry_Status'] = 'Done' if is_entered else ''
                    if is_entered and not row['Entry_Time']:
                        st.session_state.df.at[idx, 'Entry_Time'] = datetime.now().strftime("%H:%M:%S")
                    
                    # Stock
                    sz = row['T_Shirt_Size']
                    if is_given and row['T_Shirt_Collected'] == 'No':
                        st.session_state.stock[sz] -= 1
                        save_stock()
                    elif not is_given and row['T_Shirt_Collected'] == 'Yes':
                        st.session_state.stock[sz] += 1
                        save_stock()
                        
                    st.session_state.df.at[idx, 'T_Shirt_Collected'] = 'Yes' if is_given else 'No'
                    save_data()
                    st.success("Updated Successfully!")
                    time.sleep(1)
                    st.rerun()

            # --- EDIT BUTTON (ADMIN ONLY) ---
            if st.session_state.user_role == 'admin':
                with st.expander("✏️ Edit Details (Admin Only)"):
                    with st.form("edit_full"):
                        en = st.text_input("Name", row['Name'])
                        ep = st.text_input("Phone", row['Spot Phone'])
                        
                        bus_opts = ["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"]
                        curr_bus = row['Bus_Number'] if row['Bus_Number'] in bus_opts else "Unassigned"
                        eb = st.selectbox("Bus", bus_opts, index=bus_opts.index(curr_bus))
                        
                        if st.form_submit_button("Save Changes"):
                            st.session_state.df.at[idx, 'Name'] = en
                            st.session_state.df.at[idx, 'Spot Phone'] = ep
                            st.session_state.df.at[idx, 'Bus_Number'] = eb
                            save_data()
                            st.rerun()
        else:
            st.warning("User not found!")

# --- 3. ANALYTICS (GRAPHS) ---
elif menu == "📊 Analytics":
    st.title("📊 Data Analytics")
    
    tab1, tab2 = st.tabs(["🚌 Bus Stats", "👕 T-Shirt Stats"])
    
    with tab1:
        st.subheader("Bus Occupancy")
        bus_counts = st.session_state.df['Bus_Number'].value_counts()
        st.bar_chart(bus_counts)
    
    with tab2:
        st.subheader("T-Shirt Demand (Size Wise)")
        size_counts = st.session_state.df['T_Shirt_Size'].value_counts()
        st.bar_chart(size_counts)

# --- 4. STOCK (ADMIN) ---
elif menu == "👕 Stock Manager":
    st.title("📦 Inventory Control")
    # Modern Cards
    cols = st.columns(5)
    for s in ["S", "M", "L", "XL", "XXL"]:
        q = st.session_state.stock.get(s, 0)
        cols[cols.index(cols[0])+["S", "M", "L", "XL", "XXL"].index(s)].metric(s, q)
    
    with st.form("stock_upd"):
        c1, c2 = st.columns(2)
        sz = c1.selectbox("Size", ["S", "M", "L", "XL", "XXL"])
        nq = c2.number_input("New Quantity", 0)
        if st.form_submit_button("Update"):
            st.session_state.stock[sz] = nq
            save_stock()
            st.rerun()

# --- 5. BUS (ADMIN) ---
elif menu == "🚌 Bus Manager":
    st.title("🚌 Fleet Management")
    c1, c2, c3 = st.columns(3)
    grp = c1.selectbox("Group", ["Student", "Volunteer", "Teacher"])
    bus = c2.selectbox("Bus", ["Bus 1", "Bus 2", "Bus 3", "Bus 4"])
    if c3.button("🚀 Assign All", type="primary"):
        mask = st.session_state.df['Role'] == grp
        st.session_state.df.loc[mask, 'Bus_Number'] = bus
        save_data()
        st.success("Assigned!")
        st.rerun()
    
    st.dataframe(st.session_state.df[['Name', 'Role', 'Bus_Number']], use_container_width=True)

# --- 6. EXPORT (ADMIN) ---
elif menu == "📥 Export Data":
    st.title("📥 Backup & Download")
    st.write("Download the full database for offline use.")
    
    csv = st.session_state.df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name=f"Event_Data_{datetime.now().strftime('%H-%M')}.csv",
        mime='text/csv',
    )
    
