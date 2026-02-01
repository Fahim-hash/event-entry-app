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
    .info-row { display: flex; justify-content: space-between; border-bottom: 1px solid #333; padding: 8px 0; font-size: 14px; color: #ccc; }
    
    /* Input Fields Style */
    input[type="text"] {
        border: 1px solid #444 !important; background-color: #1a1a1a !important; color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== 2. DATA ENGINE ====================
conn = st.connection("gsheets", type=GSheetsConnection)

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
menu = st.sidebar.radio("Go To", ["🔍 Search & Entry", "📜 Class Lists", "🚌 Bus Manager", "📊 Dashboard", "📝 Admin Data"])

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.session_state.df = load_data()
    st.session_state.stock = load_stock()
    st.rerun()

# --- TAB 1: SEARCH & ENTRY (WITH SIZE EDIT) ---
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
            
            # Data Variables
            is_ent = row['Entry_Status'] == 'Done'
            is_kit = row['T_Shirt_Collected'] == 'Yes'
            sz = row['T_Shirt_Size']
            rem = st.session_state.stock.get(sz, 0)
            
            col1, col2 = st.columns([1, 1.5])
            
            # --- LEFT: ID CARD VISUAL ---
            with col1:
                border_c = "#00ff88" if is_ent else "#ff4b4b"
                st.markdown(f"""
                <div class="id-card" style="border: 2px solid {border_c};">
                    <div style="background:{border_c}; color:black; font-weight:bold; padding:5px; border-radius:5px;">
                        {'✅ CHECKED IN' if is_ent else '⏳ NOT ENTERED'}
                    </div>
                    <div class="id-name">{row['Name']}</div>
                    <div class="info-row"><span>Ticket:</span> <b>{row['Ticket_Number']}</b></div>
                    <div class="info-row"><span>Phone:</span> <b>{row['Spot Phone']}</b></div>
                    <div class="info-row"><span>Bus:</span> <b>{row['Bus_Number']}</b></div>
                    <div style="margin-top:10px; border:1px solid #555; padding:8px; border-radius:8px;">
                        👕 Assigned Size: <b>{sz}</b> <br>
                        Status: {'✅ GIVEN' if is_kit else f'📦 Stock: {rem}'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # --- RIGHT: EDIT & CONTROLS ---
            with col2:
                with st.container(border=True):
                    st.subheader("✏️ Edit Information")
                    
                    # Editable Fields
                    new_name = st.text_input("Name", value=row['Name'])
                    c_ph, c_tk = st.columns(2)
                    new_phone = c_ph.text_input("Spot Phone (Required)", value=row['Spot Phone'])
                    new_ticket = c_tk.text_input("Ticket No (Required)", value=row['Ticket_Number'])
                    
                    # 🔥 SIZE CHANGE OPTION 🔥
                    sz_list = ["S", "M", "L", "XL", "XXL"]
                    curr_sz_idx = sz_list.index(sz) if sz in sz_list else 2
                    new_size = st.selectbox("Update T-Shirt Size", sz_list, index=curr_sz_idx)
                    
                    st.markdown("---")
                    st.subheader("⚡ Actions")
                    
                    # Actions
                    c_a, c_b = st.columns(2)
                    new_ent = c_a.toggle("✅ Mark Entry", value=is_ent)
                    new_kit = c_b.toggle("👕 Give T-Shirt", value=is_kit)
                    
                    buses = ["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"]
                    curr_bus_idx = buses.index(row['Bus_Number']) if row['Bus_Number'] in buses else 0
                    new_bus = st.selectbox("🚌 Assign Bus", buses, index=curr_bus_idx)
                    
                    # Save Logic
                    if st.button("💾 Save Changes", type="primary", use_container_width=True):
                        # Validation
                        if not new_phone or new_phone == 'N/A' or not new_ticket or new_ticket == 'N/A':
                            st.error("❌ Error: Spot Phone and Ticket Number are REQUIRED!")
                        else:
                            # Advanced Stock Logic (Handle Size Swap)
                            if new_kit:
                                if is_kit: 
                                    if sz != new_size: # Size changed while kit already given
                                        st.session_state.stock[sz] += 1 # Return old
                                        st.session_state.stock[new_size] -= 1 # Take new
                                else: # Kit given for first time
                                    st.session_state.stock[new_size] -= 1
                            elif not new_kit and is_kit: # Kit returned/cancelled
                                st.session_state.stock[sz] += 1
                            
                            # Data Update
                            st.session_state.df.at[idx, 'Name'] = new_name
                            st.session_state.df.at[idx, 'Spot Phone'] = new_phone
                            st.session_state.df.at[idx, 'Ticket_Number'] = new_ticket
                            st.session_state.df.at[idx, 'T_Shirt_Size'] = new_size # Size Update
                            
                            st.session_state.df.at[idx, 'Entry_Status'] = 'Done' if new_ent else 'N/A'
                            st.session_state.df.at[idx, 'T_Shirt_Collected'] = 'Yes' if new_kit else 'No'
                            st.session_state.df.at[idx, 'Bus_Number'] = new_bus
                            
                            if new_ent and row['Entry_Time'] == 'N/A':
                                st.session_state.df.at[idx, 'Entry_Time'] = datetime.now().strftime("%H:%M:%S")
                            
                            # Sync
                            conn.update(worksheet="Data", data=st.session_state.df)
                            s_data = [{"Size": k, "Quantity": v} for k, v in st.session_state.stock.items()]
                            conn.update(worksheet="Stock", data=pd.DataFrame(s_data))
                            
                            st.success("✅ Updated Successfully!")
                            time.sleep(0.5)
                            st.rerun()
        else:
            st.warning("No user found!")

# --- TAB 2: CLASS LISTS (NEW FEATURE) ---
elif menu == "📜 Class Lists":
    st.title("📜 Class Wise List")
    
    # Get Unique Classes
    classes = sorted(st.session_state.df['Class'].unique().tolist())
    if '' in classes: classes.remove('')
    if 'N/A' in classes: classes.remove('N/A')
    
    selected_class = st.selectbox("Select Class:", ["All"] + classes)
    
    if selected_class == "All":
        view_df = st.session_state.df
    else:
        view_df = st.session_state.df[st.session_state.df['Class'] == selected_class]
    
    # Metrics for Class
    c1, c2, c3 = st.columns(3)
    c1.metric("Students in List", len(view_df))
    c2.metric("Checked In", len(view_df[view_df['Entry_Status'] == 'Done']))
    c3.metric("Pending", len(view_df) - len(view_df[view_df['Entry_Status'] == 'Done']))
    
    st.dataframe(view_df[['Name', 'Class', 'Roll', 'Ticket_Number', 'Spot Phone', 'Entry_Status', 'Bus_Number']], use_container_width=True)

# --- TAB 3: BUS MANAGER ---
elif menu == "🚌 Bus Manager":
    st.title("🚌 Fleet Management")
    
    cols = st.columns(4)
    buses = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    for i, b in enumerate(buses):
        cnt = len(st.session_state.df[st.session_state.df['Bus_Number'] == b])
        cols[i].metric(b, f"{cnt}/45", f"{45-cnt} Left")
    
    st.markdown("---")
    st.subheader("Auto-Assign Tool")
    c1, c2, c3 = st.columns(3)
    role = c1.selectbox("Role", ["Student", "Volunteer", "Teacher"])
    start_b = c2.selectbox("Start Bus", buses)
    
    if c3.button("🚀 Auto Assign"):
        mask = st.session_state.df['Role'] == role
        indices = st.session_state.df[mask].index.tolist()
        b_idx = buses.index(start_b)
        
        for pid in indices:
            while b_idx < 4:
                if len(st.session_state.df[st.session_state.df['Bus_Number'] == buses[b_idx]]) < 45:
                    st.session_state.df.at[pid, 'Bus_Number'] = buses[b_idx]
                    break
                else: b_idx += 1
        
        conn.update(worksheet="Data", data=st.session_state.df)
        st.success("Done!")
        st.rerun()

# --- TAB 4: DASHBOARD ---
elif menu == "📊 Dashboard":
    st.title("📊 Event Stats")
    df = st.session_state.df
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total", len(df))
    c2.metric("Checked In", len(df[df['Entry_Status']=='Done']))
    c3.metric("Kits Out", len(df[df['T_Shirt_Collected']=='Yes']))
    
    st.bar_chart(df['T_Shirt_Size'].value_counts())

# --- TAB 5: ADMIN DATA ---
elif menu == "📝 Admin Data":
    st.title("📝 Full Database")
    st.dataframe(st.session_state.df)
    
    if st.button("📥 Download CSV"):
        st.download_button("Download", st.session_state.df.to_csv(), "data.csv")
