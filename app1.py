import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# ==================== 0. PAGE CONFIG & CUSTOM CSS ====================
st.set_page_config(page_title="Event OS Ultimate", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #e0e0e0; }
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 15px; padding: 20px; border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .id-card {
        background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
        border: 2px solid #333; border-radius: 20px; padding: 20px;
        color: #fff; text-align: center; box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        margin-bottom: 10px;
    }
    .id-header { background: linear-gradient(90deg, #00c6ff, #0072ff); padding: 10px; border-radius: 10px; font-weight: bold; }
    .id-name { font-size: 28px; font-weight: 800; margin: 15px 0; }
    .id-info-row { display: flex; justify-content: space-between; border-bottom: 1px solid #333; padding: 5px 0; font-size: 14px; }
    
    /* T-shirt Visuals */
    .tshirt-badge { font-weight: bold; padding: 8px; border-radius: 8px; margin-top: 15px; font-size: 15px; border: 1px solid #fff; text-align: center; }
    .notes-box { background: rgba(255,255,255,0.05); border-left: 3px solid #ff4b4b; padding: 8px; font-size: 13px; margin: 15px 0; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

# ==================== 1. LOGIN & SESSION ====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'logs' not in st.session_state:
    st.session_state.logs = []

def add_log(msg):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, f"[{t}] {st.session_state.get('user_name', 'System')}: {msg}")

USERS = {"admin": "1234", "gate": "entry26"}

if not st.session_state.logged_in:
    st.title("🔐 Event OS Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Access"):
        if u in USERS and USERS[u] == p:
            st.session_state.logged_in = True
            st.session_state.user_name = u
            st.rerun()
    st.stop()

# ==================== 2. DATA ENGINE ====================
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Data", ttl=0)
        req_cols = ['Name', 'Role', 'Spot Phone', 'Guardian Phone', 'Ticket_Number', 'Class', 'Roll', 'Entry_Status', 'Entry_Time', 'Bus_Number', 'T_Shirt_Size', 'T_Shirt_Collected', 'Notes']
        for c in req_cols:
            if c not in df.columns: df[c] = ''
        
        # Numbers clean (Ticket/Roll .0 সরাবে)
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True).replace(['nan', 'None', ''], 'N/A')
        return df
    except:
        return pd.DataFrame()

def load_stock():
    try:
        df_s = conn.read(worksheet="Stock", ttl=0)
        stock = dict(zip(df_s['Size'], df_s['Quantity']))
        return {s: int(float(stock.get(s, 0))) for s in ["S", "M", "L", "XL", "XXL"]}
    except:
        return {"S":0, "M":0, "L":0, "XL":0, "XXL":0}

if 'df' not in st.session_state: st.session_state.df = load_data()
if 'stock' not in st.session_state: st.session_state.stock = load_stock()

# ==================== 3. NAVIGATION ====================
menu = st.sidebar.radio("Navigate", ["🏠 Dashboard", "🔍 Search & Entry", "⚙️ Admin Logs"])

# --- DASHBOARD ---
if menu == "🏠 Dashboard":
    st.title("🚀 Dashboard")
    df = st.session_state.df
    c1, c2 = st.columns(2)
    c1.metric("Total People", len(df))
    c2.metric("Checked In", len(df[df['Entry_Status'] == 'Done']))
    st.markdown("---")
    st.subheader("Bus Distribution")
    st.bar_chart(df['Bus_Number'].value_counts())

# --- SEARCH & ENTRY ---
elif menu == "🔍 Search & Entry":
    st.title("🔍 Search Terminal")
    q = st.text_input("Search by Name, Ticket or Phone:").strip()
    
    if q:
        df = st.session_state.df
        mask = df['Name'].str.contains(q, case=False) | df['Ticket_Number'].str.contains(q, case=False) | df['Spot Phone'].str.contains(q, case=False)
        res = df[mask]
        
        if not res.empty:
            idx = res.index[0]
            row = df.loc[idx]
            
            # --- T-SHIRT VISUALS ---
            sz = row['T_Shirt_Size']
            rem = st.session_state.stock.get(sz, 0)
            is_collected = row['T_Shirt_Collected'] == 'Yes'
            
            if is_collected:
                t_html = f'<div class="tshirt-badge" style="color:#00ff88; border-color:#00ff88;">👕 {sz} : ALREADY GIVEN ✅</div>'
            elif rem > 0:
                t_html = f'<div class="tshirt-badge" style="color:#00c6ff; border-color:#00c6ff;">👕 {sz} : IN STOCK ({rem}) 📦</div>'
            else:
                t_html = f'<div class="tshirt-badge" style="color:#ff4b4b; border-color:#ff4b4b;">👕 {sz} : OUT OF STOCK ❌</div>'

            # --- DIGITAL CARD ---
            st.markdown(f"""
<div class="id-card">
<div class="id-header">{'VERIFIED ENTRY' if row['Entry_Status']=='Done' else 'PENDING ENTRY'}</div>
<div class="id-name">{row['Name']}</div>
<div class="id-info-row"><span>Ticket</span><span>{row['Ticket_Number']}</span></div>
<div class="id-info-row"><span>Roll</span><span>{row['Roll']}</span></div>
<div class="id-info-row"><span>Phone</span><span>{row['Spot Phone']}</span></div>
<div class="id-info-row"><span>Bus</span><span>{row['Bus_Number']}</span></div>
{t_html}
<div class="notes-box">📝 Notes: {row['Notes']}</div>
</div>
""", unsafe_allow_html=True)
            
            with st.container(border=True):
                st.subheader("⚡ Control Panel")
                c1, c2 = st.columns(2)
                e_ent = c1.toggle("Mark Entry", value=(row['Entry_Status']=='Done'))
                e_tsh = c2.toggle("Kit Collected", value=is_collected)
                
                # Unassign Bus option
                if row['Bus_Number'] != 'Unassigned':
                    if st.button("❌ UNASSIGN BUS", use_container_width=True):
                        st.session_state.df.at[idx, 'Bus_Number'] = 'Unassigned'
                        conn.update(worksheet="Data", data=st.session_state.df)
                        st.rerun()

                if st.button("💾 Save & Sync", type="primary", use_container_width=True):
                    # Stock logic
                    if e_tsh and not is_collected: st.session_state.stock[sz] -= 1
                    elif not e_tsh and is_collected: st.session_state.stock[sz] += 1
                    
                    st.session_state.df.at[idx, 'Entry_Status'] = 'Done' if e_ent else 'N/A'
                    st.session_state.df.at[idx, 'T_Shirt_Collected'] = 'Yes' if e_tsh else 'No'
                    if e_ent and row['Entry_Time'] == 'N/A': st.session_state.df.at[idx, 'Entry_Time'] = datetime.now().strftime("%H:%M:%S")
                    
                    # Stock update spreadsheet
                    data_inv = [{"Size": k, "Quantity": v} for k, v in st.session_state.stock.items()]
                    conn.update(worksheet="Stock", data=pd.DataFrame(data_inv))
                    conn.update(worksheet="Data", data=st.session_state.df)
                    add_log(f"Updated {row['Name']}")
                    st.success("Synchronized!"); time.sleep(0.5); st.rerun()

# --- LOGS ---
elif menu == "⚙️ Admin Logs":
    st.title("📜 Activity Logs")
    for log in st.session_state.logs: st.text(log)
