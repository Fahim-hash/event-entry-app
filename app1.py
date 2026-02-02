import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time
import pytz
import streamlit.components.v1 as components

# ==================== 1. CONFIG & STYLE (ULTRA PREMIUM) ====================
st.set_page_config(page_title="Event OS Pro | Willian's 26", page_icon="🎆", layout="wide")

st.markdown("""
    <style>
    /* 🔥 BACKGROUND & SIDEBAR 🔥 */
    .stApp {
        background-color: #000000;
        background-image: linear-gradient(rgba(0, 0, 0, 0.9), rgba(0, 0, 0, 0.95)),
            url("https://images.unsplash.com/photo-1470225620780-dba8ba36b745?q=80&w=2070&auto=format&fit=crop");
        background-size: cover; background-attachment: fixed; color: #ffffff;
    }
    section[data-testid="stSidebar"] { background-color: rgba(5, 5, 5, 0.95); border-right: 1px solid #222; }

    /* === 🚀 PREMIUM ID CARDS === */
    .card-student { background: rgba(16, 30, 45, 0.7); border: 1px solid rgba(0, 255, 255, 0.2); border-radius: 16px; padding: 20px; text-align: center; }
    .card-organizer { background: linear-gradient(135deg, rgba(40, 0, 80, 0.9), rgba(10, 0, 20, 0.9)); border: 2px solid #d500f9; border-radius: 16px; padding: 20px; text-align: center; }
    .card-staff { background: linear-gradient(145deg, #002b20, #001a13); border-top: 3px solid #00ff88; border-radius: 16px; padding: 20px; text-align: center; }
    .card-elite { background: linear-gradient(to bottom, #111, #222); border: 2px solid #ffd700; padding: 20px; text-align: center; position: relative; }
    
    .id-name { font-size: 28px; font-weight: bold; margin: 12px 0; color: white; }
    .info-row { display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.1); padding: 8px 0; font-size: 14px; }
    .role-badge { background: rgba(255,255,255,0.1); padding: 4px 15px; border-radius: 20px; font-size: 11px; text-transform: uppercase; border: 1px solid rgba(255,255,255,0.2); }
    
    /* STOCK UI */
    .stock-card { background: rgba(255,255,255,0.05); border: 1px solid #444; border-radius: 10px; padding: 10px; text-align: center; }
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
    try:
        df = conn.read(worksheet="Data", ttl=0)
        req_cols = ['Name', 'Role', 'Spot Phone', 'Guardian Phone', 'Ticket_Number', 'Class', 'Roll', 'Entry_Status', 'Entry_Time', 'Bus_Number', 'T_Shirt_Size', 'T_Shirt_Collected', 'Notes']
        for c in req_cols:
            if c not in df.columns: df[c] = 'N/A'
        return df.fillna("N/A").astype(str)
    except: return pd.DataFrame()

def load_stock():
    try:
        df_s = conn.read(worksheet="Stock", ttl=0)
        return dict(zip(df_s['Size'], df_s['Quantity'].astype(int)))
    except: return {"S":0, "M":0, "L":0, "XL":0, "XXL":0}

if 'df' not in st.session_state: st.session_state.df = load_data()
if 'stock' not in st.session_state: st.session_state.stock = load_stock()

# ==================== 3. LOGIN ====================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.title("🔐 Willian's 26 | Admin")
    u, p = st.text_input("Username"), st.text_input("Password", type="password")
    if st.button("Login", type="primary"):
        if u == "admin" and p == "1234": st.session_state.logged_in = True; st.rerun()
    st.stop()

# ==================== 4. TIMER & MENU ====================
target_iso = "2026-02-03T07:00:00+06:00"
timer_html = f"""<div style="background: #000; color: #00ff88; padding: 10px; text-align: center; border-radius: 10px; border: 1px solid #00ff88;">
    <div style="font-size: 10px;">EVENT COUNTDOWN</div>
    <div id="cd" style="font-size: 20px; font-weight: bold;">-- : -- : --</div>
</div>
<script>
    const target = new Date("{target_iso}").getTime();
    setInterval(() => {{
        const now = new Date().getTime();
        const diff = target - now;
        const h = Math.floor(diff / (1000 * 60 * 60));
        const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const s = Math.floor((diff % (1000 * 60)) / 1000);
        document.getElementById("cd").innerHTML = h + "h " + m + "m " + s + "s";
    }}, 1000);
</script>"""

with st.sidebar:
    components.html(timer_html, height=80)
    menu = st.radio("Go To", ["🔍 Search & Entry", "➕ Add Staff/Teacher", "🚌 Bus Manager", "📊 Dashboard", "📝 Admin Data"])
    if st.button("🔄 Refresh"): st.cache_data.clear(); st.rerun()

# ==================== 5. MODULES ====================

if menu == "🔍 Search & Entry":
    st.title("🔍 Participant Search")
    q = st.text_input("Search by Ticket/Name/Phone:")
    if q:
        res = st.session_state.df[st.session_state.df['Name'].str.contains(q, case=False) | st.session_state.df['Ticket_Number'].str.contains(q, case=False) | st.session_state.df['Spot Phone'].str.contains(q, case=False)]
        if not res.empty:
            idx = res.index[0]; row = st.session_state.df.loc[idx]
            
            # ID CARD RENDER
            role = row['Role']
            card_class = "card-elite" if role in ["Principal", "College Head"] else "card-organizer" if role == "Organizer" else "card-staff" if "Staff" in role or "Teacher" in role else "card-student"
            
            col1, col2 = st.columns([1, 1.5])
            with col1:
                st.markdown(f"""<div class="{card_class}">
                    <div class="role-badge">{role}</div>
                    <div class="id-name">{row['Name']}</div>
                    <div class="info-row"><span>Ticket</span><span>{row['Ticket_Number']}</span></div>
                    <div class="info-row"><span>Bus</span><span>{row['Bus_Number']}</span></div>
                    <div style="color:{'#00ff88' if row['Entry_Status']=='Done' else '#ff4b4b'}; font-weight:bold; margin-top:10px;">
                        {'✅ CHECKED IN' if row['Entry_Status']=='Done' else '⏳ PENDING'}
                    </div>
                </div>""", unsafe_allow_html=True)
            
            with col2:
                with st.form("edit"):
                    st.subheader("Update Details")
                    n_name = st.text_input("Name", row['Name'])
                    n_bus = st.selectbox("Bus", ["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"], index=["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"].index(row['Bus_Number']))
                    n_size = st.selectbox("T-Shirt", ["S", "M", "L", "XL", "XXL"], index=["S", "M", "L", "XL", "XXL"].index(row['T_Shirt_Size']) if row['T_Shirt_Size'] in ["S", "M", "L", "XL", "XXL"] else 2)
                    c_a, c_b = st.columns(2)
                    n_ent = c_a.toggle("Entry", row['Entry_Status'] == 'Done')
                    n_kit = c_b.toggle("Kit Collected", row['T_Shirt_Collected'] == 'Yes')
                    
                    if st.form_submit_button("Save Changes"):
                        # Stock Logic
                        if n_kit and row['T_Shirt_Collected'] != 'Yes': st.session_state.stock[n_size] -= 1
                        elif not n_kit and row['T_Shirt_Collected'] == 'Yes': st.session_state.stock[n_size] += 1
                        
                        st.session_state.df.at[idx, 'Name'] = n_name
                        st.session_state.df.at[idx, 'Bus_Number'] = n_bus
                        st.session_state.df.at[idx, 'T_Shirt_Size'] = n_size
                        st.session_state.df.at[idx, 'Entry_Status'] = 'Done' if n_ent else 'N/A'
                        st.session_state.df.at[idx, 'T_Shirt_Collected'] = 'Yes' if n_kit else 'No'
                        
                        safe_update("Data", st.session_state.df)
                        safe_update("Stock", pd.DataFrame([{"Size": k, "Quantity": v} for k, v in st.session_state.stock.items()]))
                        st.success("Updated!"); st.rerun()

elif menu == "🚌 Bus Manager":
    st.title("🚌 Fleet & Bulk Management")
    
    # SEAT TRACKER
    cols = st.columns(4)
    for i, b in enumerate(["Bus 1", "Bus 2", "Bus 3", "Bus 4"]):
        cnt = len(st.session_state.df[st.session_state.df['Bus_Number'] == b])
        cols[i].metric(b, f"{cnt}/{BUS_CAPACITY}", f"{BUS_CAPACITY-cnt} Seats Free")
    
    # 🔥 NEW FEATURE: CLASS-WISE BULK ASSIGN 🔥
    st.markdown("---")
    st.subheader("🎯 Class-wise Bulk Assignment")
    classes = sorted([c for c in st.session_state.df['Class'].unique() if c != 'N/A'])
    c1, c2, c3 = st.columns(3)
    sel_cls = c1.selectbox("Select Class", classes)
    sel_bus = c2.selectbox("Select Bus", ["Bus 1", "Bus 2", "Bus 3", "Bus 4"])
    
    unassigned_in_class = st.session_state.df[(st.session_state.df['Class'] == sel_cls) & (st.session_state.df['Bus_Number'] == 'Unassigned')]
    
    if c3.button(f"Assign {len(unassigned_in_class)} Students"):
        free_seats = BUS_CAPACITY - len(st.session_state.df[st.session_state.df['Bus_Number'] == sel_bus])
        if free_seats >= len(unassigned_in_class):
            st.session_state.df.loc[unassigned_in_class.index, 'Bus_Number'] = sel_bus
            if safe_update("Data", st.session_state.df):
                st.success(f"Successfully moved {len(unassigned_in_class)} students to {sel_bus}!"); st.rerun()
        else: st.error("Not enough seats in this bus!")

    # MANIFEST DOWNLOAD
    if st.button("📄 Download Bus Manifest"):
        html = "<html><body>"
        for b in ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]:
            b_df = st.session_state.df[st.session_state.df['Bus_Number'] == b]
            html += f"<h2>{b} List</h2><table border='1'><tr><th>Name</th><th>Role</th><th>Phone</th></tr>"
            for _, r in b_df.iterrows(): html += f"<tr><td>{r['Name']}</td><td>{r['Role']}</td><td>{r['Spot Phone']}</td></tr>"
            html += "</table>"
        st.download_button("⬇️ Export HTML", html, "Manifest.html", "text/html")

elif menu == "📊 Dashboard":
    st.title("📊 Mission Intelligence")
    
    # 🔥 NEW FEATURE: T-SHIRT REAL-TIME STOCK CHECKER 🔥
    st.subheader("👕 T-Shirt Stock Control")
    sc = st.columns(5)
    for i, size in enumerate(["S", "M", "L", "XL", "XXL"]):
        total = st.session_state.stock.get(size, 0)
        taken = len(st.session_state.df[(st.session_state.df['T_Shirt_Size'] == size) & (st.session_state.df['T_Shirt_Collected'] == 'Yes')])
        rem = total - taken
        with sc[i]:
            st.markdown(f"""<div class="stock-card">
                <div style="font-size:12px; color:#aaa;">SIZE {size}</div>
                <div style="font-size:24px; font-weight:bold; color:{'#00ff88' if rem > 5 else '#ff4b4b'};">{rem}</div>
                <div style="font-size:10px;">Remaining of {total}</div>
            </div>""", unsafe_allow_html=True)

    # MASTER STATS
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Registered", len(st.session_state.df))
    m2.metric("Checked In", len(st.session_state.df[st.session_state.df['Entry_Status']=='Done']))
    m3.metric("Kits Distributed", len(st.session_state.df[st.session_state.df['T_Shirt_Collected']=='Yes']))

elif menu == "➕ Add Staff/Teacher":
    st.title("➕ Add Staff/Teacher")
    with st.form("add"):
        name = st.text_input("Name")
        ph = st.text_input("Phone")
        role = st.selectbox("Role", ["Teacher", "Staff", "Volunteer", "Guest"])
        if st.form_submit_button("Add Entry"):
            new = {'Name':name, 'Role':role, 'Spot Phone':ph, 'Ticket_Number':f"MAN-{int(time.time())}", 'Bus_Number':'Unassigned', 'Entry_Status':'N/A', 'T_Shirt_Collected':'No', 'T_Shirt_Size':'L'}
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new])], ignore_index=True)
            safe_update("Data", st.session_state.df)
            st.success("Added!"); st.rerun()

elif menu == "📝 Admin Data":
    st.title("📝 Master Database")
    st.dataframe(st.session_state.df, use_container_width=True)
    st.download_button("Download CSV", st.session_state.df.to_csv(index=False), "data.csv")

# FOOTER
st.sidebar.markdown("---")
st.sidebar.caption("System by Gemini AI | CineMotion")
