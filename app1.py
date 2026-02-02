import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time
import pytz
import streamlit.components.v1 as components

# ==================== 1. CONFIG & STYLE (EXACTLY AS YOUR PREVIOUS VERSION) ====================
st.set_page_config(page_title="Event OS Pro | Willian's 26", page_icon="🎆", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
        background-image: linear-gradient(rgba(0, 0, 0, 0.9), rgba(0, 0, 0, 0.95)),
            url("https://images.unsplash.com/photo-1470225620780-dba8ba36b745?q=80&w=2070&auto=format&fit=crop");
        background-size: cover; background-attachment: fixed; color: #ffffff;
    }
    section[data-testid="stSidebar"] { background-color: rgba(5, 5, 5, 0.95); border-right: 1px solid #222; }

    /* 🚀 PREMIUM CARD STYLES */
    .card-student { background: rgba(16, 30, 45, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(0, 255, 255, 0.2); border-radius: 16px; padding: 20px; text-align: center; margin-bottom: 20px; }
    .card-organizer { background: linear-gradient(135deg, rgba(40, 0, 80, 0.9), rgba(10, 0, 20, 0.9)); border: 2px solid #d500f9; border-radius: 16px; padding: 20px; text-align: center; animation: pulse-purple 2s infinite; }
    .card-staff { background: linear-gradient(145deg, #002b20, #001a13); border-top: 3px solid #00ff88; border-radius: 16px; padding: 20px; text-align: center; }
    .card-elite { background: linear-gradient(to bottom, #111, #222); border: 2px solid #ffd700; padding: 20px; text-align: center; position: relative; }
    .card-elite::after { content: "VIP ACCESS"; position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: #ffd700; color: black; font-weight: bold; font-size: 10px; padding: 2px 10px; border-radius: 10px; }

    .id-name { font-size: 28px; font-weight: bold; margin: 12px 0; color: white; }
    .info-row { display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.1); padding: 8px 0; font-size: 14px; }
    .role-badge { background: rgba(255,255,255,0.1); padding: 4px 15px; border-radius: 20px; font-size: 11px; text-transform: uppercase; border: 1px solid rgba(255,255,255,0.2); }
    
    /* 👕 STOCK UI */
    .stock-box { background: rgba(255,255,255,0.05); border-left: 4px solid #00ff88; padding: 10px; border-radius: 8px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# ==================== 2. DATA ENGINE ====================
conn = st.connection("gsheets", type=GSheetsConnection)
BUS_CAPACITY = 45

def safe_update(ws, data):
    try:
        conn.update(worksheet=ws, data=data)
        return True
    except Exception as e:
        st.error(f"⚠️ Sync Error: {e}")
        return False

def load_data():
    df = conn.read(worksheet="Data", ttl=0)
    for col in df.columns: df[col] = df[col].astype(str).replace(['nan', 'None', ''], 'N/A')
    return df

def load_stock():
    try:
        df_s = conn.read(worksheet="Stock", ttl=0)
        return dict(zip(df_s['Size'], df_s['Quantity'].astype(int)))
    except: return {"S":100, "M":100, "L":100, "XL":100, "XXL":100} # Default if sheet missing

if 'df' not in st.session_state: st.session_state.df = load_data()
if 'stock' not in st.session_state: st.session_state.stock = load_stock()

# ==================== 3. LOGIN & TIMER ====================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.title("🔐 Admin Gateway")
    u, p = st.text_input("User"), st.text_input("Pass", type="password")
    if st.button("Login"):
        if u == "admin" and p == "1234": st.session_state.logged_in = True; st.rerun()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚡ Control")
    menu = st.radio("Go To", ["🔍 Search & Entry", "➕ Add Staff", "🚌 Bus Manager", "📊 Dashboard", "📝 Admin Data"])

# ==================== 4. MODULES (INTEGRATED FEATURES) ====================

if menu == "🔍 Search & Entry":
    st.title("🔍 Search System")
    q = st.text_input("Ticket / Name / Phone:").strip()
    if q:
        df = st.session_state.df
        res = df[df['Name'].str.contains(q, case=False) | df['Ticket_Number'].str.contains(q, case=False) | df['Spot Phone'].str.contains(q, case=False)]
        if not res.empty:
            idx = res.index[0]; row = df.loc[idx]
            
            # --- CARD RENDER ---
            role = row['Role']
            card_class = "card-elite" if role in ["Principal", "College Head"] else "card-organizer" if role == "Organizer" else "card-staff" if "Staff" in role or "Teacher" in role else "card-student"
            
            col1, col2 = st.columns([1, 1.5])
            with col1:
                st.markdown(f"""<div class="{card_class}">
                    <div class="role-badge">{role}</div>
                    <div class="id-name">{row['Name']}</div>
                    <div class="info-row"><span>Ticket</span><span>{row['Ticket_Number']}</span></div>
                    <div class="info-row"><span>Size</span><span>{row['T_Shirt_Size']}</span></div>
                    <div style="color:{'#00ff88' if row['Entry_Status']=='Done' else '#ff4b4b'}; font-weight:bold; margin-top:10px;">
                        {'✅ CHECKED IN' if row['Entry_Status']=='Done' else '⏳ NOT ENTERED'}
                    </div>
                </div>""", unsafe_allow_html=True)

            with col2:
                with st.form("edit_form"):
                    st.subheader("Update Record")
                    new_size = st.selectbox("T-Shirt Size", ["S", "M", "L", "XL", "XXL"], index=["S", "M", "L", "XL", "XXL"].index(row['T_Shirt_Size']) if row['T_Shirt_Size'] in ["S", "M", "L", "XL", "XXL"] else 2)
                    new_bus = st.selectbox("Bus Assignment", ["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"], index=["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"].index(row['Bus_Number']))
                    c1, c2 = st.columns(2)
                    n_ent = c1.toggle("Entry", row['Entry_Status'] == 'Done')
                    n_kit = c2.toggle("Kit Collected", row['T_Shirt_Collected'] == 'Yes')
                    
                    if st.form_submit_button("💾 Save Update"):
                        # 👕 STOCK LOGIC (Auto-Deduct/Add)
                        if n_kit and row['T_Shirt_Collected'] != 'Yes': 
                            st.session_state.stock[new_size] -= 1
                        elif not n_kit and row['T_Shirt_Collected'] == 'Yes': 
                            st.session_state.stock[new_size] += 1
                        
                        st.session_state.df.at[idx, 'T_Shirt_Size'] = new_size
                        st.session_state.df.at[idx, 'Bus_Number'] = new_bus
                        st.session_state.df.at[idx, 'Entry_Status'] = 'Done' if n_ent else 'N/A'
                        st.session_state.df.at[idx, 'T_Shirt_Collected'] = 'Yes' if n_kit else 'No'
                        
                        safe_update("Data", st.session_state.df)
                        safe_update("Stock", pd.DataFrame([{"Size": k, "Quantity": v} for k, v in st.session_state.stock.items()]))
                        st.success("Updated Successfully!"); st.rerun()

elif menu == "🚌 Bus Manager":
    st.title("🚌 Fleet Management")
    
    # 🎯 CLASS ASSIGN LOGIC (NEW)
    st.subheader("🎯 Class-wise Bulk Assign")
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        all_cls = sorted([c for c in st.session_state.df['Class'].unique() if c != 'N/A'])
        sel_cls = c1.selectbox("Filter Class", all_cls)
        sel_bus = c2.selectbox("Destination Bus", ["Bus 1", "Bus 2", "Bus 3", "Bus 4"])
        
        pending = st.session_state.df[(st.session_state.df['Class'] == sel_cls) & (st.session_state.df['Bus_Number'] == 'Unassigned')]
        
        if c3.button(f"Move {len(pending)} Persons"):
            free = BUS_CAPACITY - len(st.session_state.df[st.session_state.df['Bus_Number'] == sel_bus])
            if free >= len(pending):
                st.session_state.df.loc[pending.index, 'Bus_Number'] = sel_bus
                safe_update("Data", st.session_state.df)
                st.success(f"Moved {len(pending)} students to {sel_bus}!"); st.rerun()
            else: st.error("Bus Full!")

    st.markdown("---")
    # Fleet Stats
    cols = st.columns(4)
    for i, b in enumerate(["Bus 1", "Bus 2", "Bus 3", "Bus 4"]):
        cnt = len(st.session_state.df[st.session_state.df['Bus_Number'] == b])
        cols[i].metric(b, f"{cnt}/{BUS_CAPACITY}", f"{BUS_CAPACITY-cnt} Free")

elif menu == "📊 Dashboard":
    st.title("📊 Mission Stats")
    
    # 👕 T-SHIRT STOCK CHECKER (NEW)
    st.subheader("👕 Real-time T-Shirt Inventory")
    sc = st.columns(5)
    for i, size in enumerate(["S", "M", "L", "XL", "XXL"]):
        total = st.session_state.stock.get(size, 0)
        # Count only those who have "Collected = Yes"
        given = len(st.session_state.df[(st.session_state.df['T_Shirt_Size'] == size) & (st.session_state.df['T_Shirt_Collected'] == 'Yes')])
        rem = total - given
        with sc[i]:
            st.markdown(f"""<div class="stock-box">
                <div style="font-size:11px; color:#aaa;">SIZE {size}</div>
                <div style="font-size:22px; font-weight:bold; color:{'#00ff88' if rem > 5 else '#ff4b4b'};">{rem}</div>
                <div style="font-size:10px;">Remaining</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total", len(st.session_state.df))
    m2.metric("Checked In", len(st.session_state.df[st.session_state.df['Entry_Status']=='Done']))
    m3.metric("Kits Given", len(st.session_state.df[st.session_state.df['T_Shirt_Collected']=='Yes']))

elif menu == "📝 Admin Data":
    st.title("📝 Full Records")
    st.dataframe(st.session_state.df, use_container_width=True)
    st.download_button("Export CSV", st.session_state.df.to_csv(index=False), "data.csv")

elif menu == "➕ Add Staff":
    st.title("➕ Add Staff/Teacher")
    with st.form("add"):
        name = st.text_input("Full Name")
        ph = st.text_input("Phone Number")
        role = st.selectbox("Role", ["Teacher", "Staff", "Volunteer", "Guest"])
        if st.form_submit_button("Add Record"):
            new_row = {'Name':name, 'Role':role, 'Spot Phone':ph, 'Ticket_Number':f"MAN-{int(time.time())}", 'Bus_Number':'Unassigned', 'Entry_Status':'N/A', 'T_Shirt_Collected':'No', 'T_Shirt_Size':'L', 'Class':'N/A'}
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
            safe_update("Data", st.session_state.df)
            st.success("Added!"); st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("System V4.0 | Willian's 26")
