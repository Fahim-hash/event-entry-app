import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# Page Config
st.set_page_config(page_title="Event Cloud System", page_icon="☁️", layout="wide")

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

BUS_CAPACITY = 45
conn = st.connection("gsheets", type=GSheetsConnection)

# --- LOAD DATA FUNCTIONS ---
def load_data():
    try:
        df = conn.read(worksheet="Data", ttl=0)
        cols = ['Name', 'Role', 'Spot Phone', 'Ticket_Number', 'Class', 'Roll', 'Entry_Status', 'Entry_Time', 'Bus_Number', 'T_Shirt_Size', 'T_Shirt_Collected', 'Notes']
        for c in cols:
            if c not in df.columns: df[c] = ''
        # Ticket Number এবং Phone কে String এ কনভার্ট করা যাতে সার্চে সমস্যা না হয়
        df['Ticket_Number'] = df['Ticket_Number'].astype(str)
        df['Spot Phone'] = df['Spot Phone'].astype(str)
        return df.fillna('')
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        return pd.DataFrame(columns=['Name', 'Role', 'Class', 'Ticket_Number', 'Spot Phone'])

def load_stock():
    try:
        df_s = conn.read(worksheet="Stock", ttl=0)
        stock = dict(zip(df_s['Size'], df_s['Quantity']))
        for s in ["S", "M", "L", "XL", "XXL"]:
            if s not in stock: stock[s] = 0
        return stock
    except Exception as e:
        st.error(f"Stock Load Error: {e}")
        return {"S":0, "M":0, "L":0, "XL":0, "XXL":0}

if 'df' not in st.session_state:
    st.session_state.df = load_data()
if 'stock' not in st.session_state:
    st.session_state.stock = load_stock()

# --- SAVE FUNCTIONS ---
def save_data():
    try:
        conn.update(worksheet="Data", data=st.session_state.df)
        st.toast("✅ Data Saved to Cloud!")
    except Exception as e:
        st.error(f"Save Error: {e}")

def save_stock():
    try:
        data = [{"Size": k, "Quantity": v} for k, v in st.session_state.stock.items()]
        conn.update(worksheet="Stock", data=pd.DataFrame(data))
    except Exception as e:
        st.error(f"Stock Save Error: {e}")

# --- HELPER FUNCTIONS ---
def add_new_person(name, role, phone, ticket):
    # Validation Check
    if not phone.strip():
        st.error("❌ Phone Number is Required!")
        return
    if not ticket.strip():
        st.error("❌ Ticket Number is Required!")
        return

    new_data = {
        'Name': name, 'Role': role, 'Spot Phone': str(phone), 'Ticket_Number': str(ticket),
        'Class': 'Teacher/Guest' if role in ['Teacher', 'Guest'] else 'New Entry',
        'Roll': 'N/A', 'Entry_Status': '', 'Entry_Time': '', 'Bus_Number': 'Unassigned',
        'T_Shirt_Size': 'L', 'T_Shirt_Collected': 'No', 'Notes': 'Added Online'
    }
    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_data])], ignore_index=True)
    save_data()
    st.success("✅ Added Successfully!")
    st.rerun()

def assign_bus_bulk(group_type, group_value, bus_num):
    mask = st.session_state.df['Class'] == group_value if group_type == "Class" else st.session_state.df['Role'] == group_value
    if mask.any():
        st.session_state.df.loc[mask, 'Bus_Number'] = bus_num
        save_data()
        return mask.sum()
    return 0

# ==================== 3. UI & NAVIGATION ====================

st.sidebar.title("☁️ Cloud System")
if st.sidebar.button("🔄 Refresh Data"):
    st.session_state.df = load_data()
    st.session_state.stock = load_stock()
    st.rerun()

menu = st.sidebar.radio("Go to:", ["🔍 Dashboard & Search", "👕 T-Shirt Stock", "🚌 Bus Distribution", "👨‍🏫 Teachers & Guests", "🎗️ Staff (Vol/Org)", "📂 Class Section List", "📊 Live Status"])

st.sidebar.markdown("---")
with st.sidebar.expander("➕ Add New Person"):
    with st.form("add_person_form"):
        new_name = st.text_input("Name")
        new_role = st.selectbox("Role", ["Student", "Teacher", "Guest", "Volunteer", "Organizer"])
        new_phone = st.text_input("Phone (Required)")
        new_ticket = st.text_input("Ticket No (Required)")
        
        if st.form_submit_button("Add Person"):
            add_new_person(new_name, new_role, new_phone, new_ticket)

# --- OPTION 1: DASHBOARD ---
if menu == "🔍 Dashboard & Search":
    st.title("🚀 Event Dashboard")
    
    total = len(st.session_state.df)
    entered = len(st.session_state.df[st.session_state.df['Entry_Status'] == 'Done'])
    tshirts = len(st.session_state.df[st.session_state.df['T_Shirt_Collected'] == 'Yes'])
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 Total", total)
    c2.metric("✅ Entered", entered)
    c3.metric("👕 Given", tshirts)
    c4.metric("⏳ Pending", total - entered)
    st.progress(entered / total if total > 0 else 0)
    
    st.markdown("---")
    
    # SEARCH SECTION (UPDATED FOR TICKET SEARCH)
    query = st.text_input("🔍 Search (Name, Ticket, Roll):", placeholder="Type Name or Ticket Number...")
    
    if query:
        # Convert columns to string before searching to avoid errors
        res = st.session_state.df[
            st.session_state.df['Name'].astype(str).str.contains(query, case=False, na=False) | 
            st.session_state.df['Ticket_Number'].astype(str).str.contains(query, case=False, na=False) |
            st.session_state.df['Roll'].astype(str).str.contains(query, case=False, na=False)
        ]
        
        if not res.empty:
            idx = res.index[0]
            if len(res) > 1:
                sel = st.selectbox("Select Person:", res['Name'].tolist())
                idx = res[res['Name'] == sel].index[0]
            
            row = st.session_state.df.loc[idx]
            
            # --- PROFILE CARD ---
            with st.container(border=True):
                st.subheader(f"{row['Name']} ({row['Role']})")
                
                # Ticket Number Display
                st.write(f"🎟 Ticket: **{row['Ticket_Number']}**")
                
                # Stock Logic Display
                sz = row['T_Shirt_Size']
                is_given = row['T_Shirt_Collected'] == 'Yes'
                rem_stock = st.session_state.stock.get(sz, 0)
                
                col_a, col_b = st.columns(2)
                if is_given: col_a.success(f"👕 {sz} (GIVEN)")
                else:
                    if rem_stock > 0: col_a.info(f"👕 {sz} (Available: {rem_stock})")
                    else: col_a.error(f"👕 {sz} (OUT OF STOCK)")
                
                if row['Entry_Status'] == 'Done': col_b.success("✅ ENTERED")
                else: col_b.warning("⏳ PENDING")

            # --- EDIT FORM (UPDATED) ---
            st.markdown("### ✏️ Edit Details")
            with st.form("edit_form"):
                c1, c2 = st.columns(2)
                n_name = c1.text_input("Name", value=row['Name'])
                n_phone = c2.text_input("Phone (Required)", value=row['Spot Phone'])
                
                c3, c4 = st.columns(2)
                # Ticket is now EDITABLE
                n_ticket = c3.text_input("Ticket Number (Required)", value=row['Ticket_Number'])
                n_bus = c4.selectbox("Bus", ["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"], index=["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"].index(row['Bus_Number']) if row['Bus_Number'] in ["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"] else 0)
                
                st.markdown("---")
                ct1, ct2, ct3 = st.columns(3)
                n_size = ct1.selectbox("Size", ["S", "M", "L", "XL", "XXL"], index=["S", "M", "L", "XL", "XXL"].index(sz) if sz in ["S", "M", "L", "XL", "XXL"] else 2)
                n_given = ct2.checkbox("✅ T-Shirt GIVEN", value=is_given)
                n_enter = ct3.checkbox("✅ Mark ENTERED", value=(row['Entry_Status']=='Done'))
                
                if st.form_submit_button("💾 Update"):
                    # VALIDATION CHECK inside form
                    if not n_phone.strip():
                        st.error("❌ Phone Number cannot be empty!")
                    elif not n_ticket.strip():
                        st.error("❌ Ticket Number cannot be empty!")
                    else:
                        st.session_state.df.at[idx, 'Name'] = n_name
                        st.session_state.df.at[idx, 'Spot Phone'] = n_phone
                        st.session_state.df.at[idx, 'Ticket_Number'] = n_ticket
                        st.session_state.df.at[idx, 'Bus_Number'] = n_bus
                        st.session_state.df.at[idx, 'T_Shirt_Size'] = n_size
                        
                        # Stock Logic
                        if n_given and not is_given:
                            st.session_state.stock[sz] -= 1
                            save_stock()
                        elif not n_given and is_given:
                            st.session_state.stock[sz] += 1
                            save_stock()
                        
                        st.session_state.df.at[idx, 'T_Shirt_Collected'] = 'Yes' if n_given else 'No'
                        st.session_state.df.at[idx, 'Entry_Status'] = 'Done' if n_enter else ''
                        
                        if n_enter and not row['Entry_Time']:
                            st.session_state.df.at[idx, 'Entry_Time'] = datetime.now().strftime("%H:%M:%S")
                        
                        save_data()
                        st.success("Updated Successfully!")
                        st.rerun()
        else:
            st.warning("No record found!")

# --- OPTION 2: STOCK ---
elif menu == "👕 T-Shirt Stock":
    st.title("👕 Stock Management")
    dist = st.session_state.df[st.session_state.df['T_Shirt_Collected'] == 'Yes']['T_Shirt_Size'].value_counts()
    
    cols = st.columns(5)
    for s in ["S", "M", "L", "XL", "XXL"]:
        rem = st.session_state.stock.get(s, 0) - dist.get(s, 0)
        cols[cols.index(cols[0])+["S", "M", "L", "XL", "XXL"].index(s)].metric(s, rem, delta=f"Given: {dist.get(s, 0)}", delta_color="inverse")
    
    st.markdown("---")
    with st.form("stk_form"):
        c1, c2 = st.columns(2)
        sz = c1.selectbox("Size", ["S", "M", "L", "XL", "XXL"])
        q = c2.number_input("New Total Quantity", value=st.session_state.stock.get(sz, 0))
        if st.form_submit_button("Update Stock"):
            st.session_state.stock[sz] = q
            save_stock()
            st.rerun()

# --- OPTION 3: BUS ---
elif menu == "🚌 Bus Distribution":
    st.title("🚌 Bus Management")
    cols = st.columns(4)
    buses = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    for i, b in enumerate(buses):
        c = len(st.session_state.df[st.session_state.df['Bus_Number'] == b])
        cols[i].metric(b, f"{c}/{BUS_CAPACITY}")
        cols[i].progress(min(c/BUS_CAPACITY, 1.0))
        if c > BUS_CAPACITY: cols[i].error("OVERFLOW")
    
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    t = c1.selectbox("Type", ["Class", "Role"])
    grp_opts = sorted(st.session_state.df['Class'].unique()) if t=="Class" else ["Teacher", "Volunteer", "Organizer", "Guest", "Student"]
    grp = c2.selectbox("Group", ["Select..."] + list(grp_opts))
    bus = c3.selectbox("Bus", buses)
    if c4.button("🚀 Assign") and grp != "Select...":
        assign_bus_bulk(t, grp, bus)
        st.success("Moved!")
        st.rerun()
    
    tabs = st.tabs(["Unassigned"] + buses)
    with tabs[0]: st.dataframe(st.session_state.df[st.session_state.df['Bus_Number'].isin(['Unassigned', ''])][['Name', 'Class', 'Role']])
    for i, b in enumerate(buses):
        with tabs[i+1]: st.dataframe(st.session_state.df[st.session_state.df['Bus_Number'] == b][['Name', 'Role', 'Spot Phone']])

# --- OPTION 4-6: LISTS ---
elif menu == "👨‍🏫 Teachers & Guests":
    st.title("👨‍🏫 Teachers & Guests")
    df_t = st.session_state.df[st.session_state.df['Role'].isin(["Teacher", "Guest"])]
    st.dataframe(df_t[['Name', 'Role', 'Bus_Number', 'Spot Phone']])
    
    st.subheader("Quick Bus Assign")
    c1, c2, c3 = st.columns([2, 1, 1])
    tn = c1.selectbox("Name", ["Select..."] + df_t['Name'].tolist())
    tb = c2.selectbox("Bus", ["Bus 1", "Bus 2", "Bus 3", "Bus 4", "Unassigned"])
    if c3.button("Update") and tn != "Select...":
        idx = st.session_state.df[st.session_state.df['Name'] == tn].index[0]
        st.session_state.df.at[idx, 'Bus_Number'] = tb
        save_data()
        st.rerun()

elif menu == "🎗️ Staff (Vol/Org)":
    st.title("🎗️ Staff")
    st.dataframe(st.session_state.df[st.session_state.df['Role'].isin(["Volunteer", "Organizer"])][['Name', 'Role', 'Bus_Number']])

elif menu == "📂 Class Section List":
    cl = st.selectbox("Class", ["Select"] + sorted(st.session_state.df['Class'].unique()))
    if cl != "Select": st.dataframe(st.session_state.df[st.session_state.df['Class'] == cl])

elif menu == "📊 Live Status":
    st.title("📊 Live Feed")
    st.dataframe(st.session_state.df[st.session_state.df['Entry_Status'] == 'Done'][['Name', 'Entry_Time', 'Bus_Number', 'T_Shirt_Size']])
