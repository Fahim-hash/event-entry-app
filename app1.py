import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# Page Config
st.set_page_config(page_title="Event Entry Cloud", page_icon="☁️", layout="wide")

# ==================== 1. LOGIN SYSTEM ====================
USERS = {
    "admin": "1234",      # মেইন এডমিন
    "gate": "entry26"     # গেটের ভলান্টিয়ার
}

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def check_login():
    user = st.session_state['username']
    pwd = st.session_state['password']
    if user in USERS and USERS[user] == pwd:
        st.session_state.logged_in = True
        st.success("Login Successful!")
        st.rerun()
    else:
        st.error("❌ ভুল ইউজারনেম বা পাসওয়ার্ড")

if not st.session_state.logged_in:
    st.title("🔒 Login Required")
    st.text_input("Username", key="username")
    st.text_input("Password", type="password", key="password")
    st.button("Login", on_click=check_login)
    st.stop()

# ==================== 2. GOOGLE SHEETS CONNECTION ====================

# Constants
BUS_CAPACITY = 45

# Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNCTION: LOAD DATA ---
def load_data():
    # 'Data' ট্যাব থেকে স্টুডেন্ট লিস্ট লোড
    try:
        df = conn.read(worksheet="Data", ttl=0) # ttl=0 মানে সবসময় ফ্রেশ ডাটা আনবে
        # কলাম ঠিক আছে কিনা চেক করা
        cols = ['Name', 'Role', 'Spot Phone', 'Ticket_Number', 'Class', 'Roll', 'Entry_Status', 'Entry_Time', 'Bus_Number', 'T_Shirt_Size', 'T_Shirt_Collected', 'Notes']
        for c in cols:
            if c not in df.columns: df[c] = ''
        return df.fillna('')
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        return pd.DataFrame()

def load_stock():
    # 'Stock' ট্যাব থেকে স্টক লোড
    try:
        df_s = conn.read(worksheet="Stock", ttl=0)
        stock = dict(zip(df_s['Size'], df_s['Quantity']))
        for s in ["S", "M", "L", "XL", "XXL"]:
            if s not in stock: stock[s] = 0
        return stock
    except Exception as e:
        st.error(f"Stock Load Error: {e}")
        return {"S":0, "M":0, "L":0, "XL":0, "XXL":0}

# Session State-এ ডাটা রাখা (যাতে বারবার লোড না হয়)
if 'df' not in st.session_state:
    st.session_state.df = load_data()
if 'stock' not in st.session_state:
    st.session_state.stock = load_stock()

# --- FUNCTION: SAVE DATA ---
def save_data():
    try:
        conn.update(worksheet="Data", data=st.session_state.df)
        st.toast("✅ Data Saved to Google Sheet!")
    except Exception as e:
        st.error(f"Save Error: {e}")

def save_stock():
    try:
        # Dictionary থেকে DataFrame বানিয়ে সেভ করা
        data = [{"Size": k, "Quantity": v} for k, v in st.session_state.stock.items()]
        conn.update(worksheet="Stock", data=pd.DataFrame(data))
    except Exception as e:
        st.error(f"Stock Save Error: {e}")

# --- FUNCTION: BULK BUS ASSIGN ---
def bulk_assign(by, val, bus):
    mask = st.session_state.df['Class'] == val if by == "Class" else st.session_state.df['Role'] == val
    if mask.any():
        st.session_state.df.loc[mask, 'Bus_Number'] = bus
        save_data()
        return mask.sum()
    return 0

# ==================== 3. UI & NAVIGATION ====================

st.sidebar.title("☁️ Cloud Entry")
if st.sidebar.button("🔄 Refresh Data (Cloud)"):
    st.session_state.df = load_data()
    st.session_state.stock = load_stock()
    st.rerun()

menu = st.sidebar.radio("Go to:", ["Dashboard", "T-Shirt Stock", "Bus Plan", "Teachers/Guest", "Staff", "Class List", "Live Status"])

# --- MENU: DASHBOARD ---
if menu == "Dashboard":
    st.title("🚀 Event Dashboard")
    
    # Metrics
    tot = len(st.session_state.df)
    ent = len(st.session_state.df[st.session_state.df['Entry_Status'] == 'Done'])
    tsh = len(st.session_state.df[st.session_state.df['T_Shirt_Collected'] == 'Yes'])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("👥 Total", tot)
    c2.metric("✅ Entered", ent)
    c3.metric("👕 Given", tsh)
    st.progress(ent/tot if tot>0 else 0)
    
    st.markdown("---")
    
    # Search & Update
    query = st.text_input("🔍 Search Student/Guest (Name or Ticket):")
    if query:
        res = st.session_state.df[st.session_state.df['Name'].str.contains(query, case=False) | st.session_state.df['Ticket_Number'].str.contains(query, case=False)]
        if not res.empty:
            idx = res.index[0]
            row = st.session_state.df.loc[idx]
            
            with st.container(border=True):
                st.subheader(f"{row['Name']} ({row['Role']})")
                st.write(f"🎟 Ticket: `{row['Ticket_Number']}` | 🚌 Bus: **{row['Bus_Number']}**")
                st.info(f"Size: {row['T_Shirt_Size']}")
                
                c_a, c_b = st.columns(2)
                check_ent = c_a.checkbox("✅ Entered", value=(row['Entry_Status']=='Done'), key="ent")
                check_tsh = c_b.checkbox("👕 T-Shirt Given", value=(row['T_Shirt_Collected']=='Yes'), key="tsh")
                
                if st.button("Update Status"):
                    # 1. Update Entry
                    st.session_state.df.at[idx, 'Entry_Status'] = 'Done' if check_ent else ''
                    if check_ent and not row['Entry_Time']:
                        st.session_state.df.at[idx, 'Entry_Time'] = datetime.now().strftime("%H:%M:%S")
                    
                    # 2. Update Stock (Logic)
                    sz = row['T_Shirt_Size']
                    if check_tsh and row['T_Shirt_Collected'] == 'No':
                        st.session_state.stock[sz] -= 1 # কমে যাবে
                        save_stock()
                    elif not check_tsh and row['T_Shirt_Collected'] == 'Yes':
                        st.session_state.stock[sz] += 1 # ফেরত আসবে
                        save_stock()
                    
                    st.session_state.df.at[idx, 'T_Shirt_Collected'] = 'Yes' if check_tsh else 'No'
                    save_data()
                    st.success("Updated Successfully!")
                    st.rerun()

# --- MENU: STOCK ---
elif menu == "T-Shirt Stock":
    st.title("👕 Stock Management")
    
    # Display Stock Cards
    cols = st.columns(5)
    for s in ["S", "M", "L", "XL", "XXL"]:
        qty = st.session_state.stock.get(s, 0)
        cols[cols.index(cols[0])+["S", "M", "L", "XL", "XXL"].index(s)].metric(s, qty)
    
    st.markdown("---")
    st.subheader("Update Stock Manually")
    with st.form("stk_form"):
        sz = st.selectbox("Size", ["S", "M", "L", "XL", "XXL"])
        q = st.number_input("New Quantity", value=0)
        if st.form_submit_button("Update Stock"):
            st.session_state.stock[sz] = q
            save_stock()
            st.rerun()

# --- MENU: BUS PLAN ---
elif menu == "Bus Plan":
    st.title("🚌 Bus Management")
    
    # Metrics
    cols = st.columns(4)
    buses = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    for i, b in enumerate(buses):
        c = len(st.session_state.df[st.session_state.df['Bus_Number'] == b])
        cols[i].metric(b, f"{c}/{BUS_CAPACITY}")
        if c > BUS_CAPACITY: cols[i].error("OVERFLOW")
        else: cols[i].progress(min(c/BUS_CAPACITY, 1.0))
    
    st.markdown("---")
    
    # Bulk Assign
    c1, c2, c3 = st.columns(3)
    typ = c1.selectbox("Type", ["Class", "Role"])
    grp_opts = sorted(st.session_state.df['Class'].unique()) if typ=="Class" else ["Teacher", "Volunteer", "Student", "Guest"]
    grp = c2.selectbox("Select Group", ["Select..."] + list(grp_opts))
    bus = c3.selectbox("Assign Bus", buses)
    
    if st.button("🚀 Bulk Assign") and grp != "Select...":
        n = bulk_assign(typ, grp, bus)
        st.success(f"Moved {n} people to {bus}!")
        st.rerun()
        
    # Unassigned List
    st.markdown("### Unassigned People")
    st.dataframe(st.session_state.df[st.session_state.df['Bus_Number'].isin(['Unassigned', ''])][['Name', 'Role', 'Class']])

# --- MENU: TEACHERS ---
elif menu == "Teachers/Guest":
    st.title("👨‍🏫 Teachers & Guests")
    df_t = st.session_state.df[st.session_state.df['Role'].isin(['Teacher', 'Guest'])]
    st.dataframe(df_t[['Name', 'Role', 'Bus_Number', 'Spot Phone']])
    
    st.subheader("Quick Bus Assign")
    c1, c2, c3 = st.columns([2, 1, 1])
    t_name = c1.selectbox("Name", ["Select..."] + df_t['Name'].tolist())
    t_bus = c2.selectbox("Bus", ["Bus 1", "Bus 2", "Bus 3", "Bus 4"])
    
    if c3.button("Update") and t_name != "Select...":
        idx = st.session_state.df[st.session_state.df['Name'] == t_name].index[0]
        st.session_state.df.at[idx, 'Bus_Number'] = t_bus
        save_data()
        st.rerun()

# --- MENU: STAFF ---
elif menu == "Staff":
    st.title("🎗️ Volunteers & Organizers")
    st.dataframe(st.session_state.df[st.session_state.df['Role'].isin(['Volunteer', 'Organizer'])][['Name', 'Role', 'Bus_Number']])

# --- MENU: LIVE STATUS ---
elif menu == "Live Status":
    st.title("📊 Live Entry Feed")
    st.dataframe(st.session_state.df[st.session_state.df['Entry_Status'] == 'Done'][['Name', 'Entry_Time', 'Bus_Number']])

# --- MENU: CLASS LIST ---
elif menu == "Class List":
    cl = st.selectbox("Select Class", ["Select"] + sorted(st.session_state.df['Class'].unique()))
    if cl != "Select":
        st.dataframe(st.session_state.df[st.session_state.df['Class'] == cl])