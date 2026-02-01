import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time
import altair as alt

# --- PAGE CONFIG ---
st.set_page_config(page_title="Event OS Ultimate", page_icon="⚡", layout="wide")

# --- CUSTOM CSS FOR PREMIUM LOOK ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #e0e0e0; }
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px; padding: 20px; border: 1px solid #333;
    }
    .id-card {
        background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
        border-radius: 20px; padding: 25px; text-align: center;
        border: 2px solid #45a29e; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .id-role { background: #ff4b4b; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN & DATA ENGINE ---
USERS = {
    "admin": {"password": "1234", "role": "admin", "name": "Super Admin"},
    "gate": {"password": "entry26", "role": "volunteer", "name": "Gate Volunteer"}
}

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def check_login():
    u, p = st.session_state['username'], st.session_state['password']
    if u in USERS and USERS[u]["password"] == p:
        st.session_state.logged_in, st.session_state.user_role = True, USERS[u]["role"]
        st.session_state.user_name = USERS[u]["name"]
        st.rerun()

if not st.session_state.logged_in:
    st.title("🔒 Event OS Login")
    st.text_input("Username", key="username")
    st.text_input("Password", type="password", key="password")
    st.button("🚀 Access System", on_click=check_login)
    st.stop()

# --- GOOGLE SHEETS CONNECTION ---
BUS_CAPACITY = 45
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    df = conn.read(worksheet="Data", ttl=0)
    # ডাটা টাইপ ফিক্স করা
    for col in ['Ticket_Number', 'Spot Phone', 'Guardian Phone', 'Roll', 'Class']:
        df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().replace('nan', 'N/A')
    return df.fillna('')

def load_stock():
    df_s = conn.read(worksheet="Stock", ttl=0)
    stock = dict(zip(df_s['Size'], df_s['Quantity']))
    return {s: stock.get(s, 0) for s in ["S", "M", "L", "XL", "XXL"]}

if 'df' not in st.session_state: st.session_state.df = load_data()
if 'stock' not in st.session_state: st.session_state.stock = load_stock()

# --- NAVIGATION ---
st.sidebar.title(f"👋 {st.session_state.user_name}")
menu = st.sidebar.radio("Navigate", ["🏠 Dashboard", "🔍 Search & Entry", "👨‍🏫 Teachers", "🚌 Bus Fleet", "📦 Stock", "⚙️ Admin Logs"])

# --- MODULES ---
if menu == "🏠 Dashboard":
    st.title("🚀 Live Dashboard")
    df = st.session_state.df
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", len(df))
    c2.metric("Checked In", len(df[df['Entry_Status']=='Done']))
    c3.metric("Kits Given", len(df[df['T_Shirt_Collected']=='Yes']))
    c4.metric("Meals Served", len(df[df.get('Food_Collected', '')=='Yes']))
    
    # Live Entry Chart
    if not df[df['Entry_Status']=='Done'].empty:
        st.markdown("### 📈 Entry Traffic")
        chart_df = df[df['Entry_Status']=='Done'].copy()
        chart_df['Hour'] = pd.to_datetime(chart_df['Entry_Time']).dt.hour
        st.line_chart(chart_df['Hour'].value_counts())

elif menu == "🔍 Search & Entry":
    st.title("🔍 Search Terminal")
    q = st.text_input("Search (Ticket/Name/Phone/Guardian):").strip()
    if q:
        mask = (st.session_state.df['Name'].str.contains(q, case=False) | st.session_state.df['Ticket_Number'].str.contains(q, case=False) | st.session_state.df['Spot Phone'].str.contains(q, case=False) | st.session_state.df['Guardian Phone'].str.contains(q, case=False))
        res = st.session_state.df[mask]
        if not res.empty:
            idx = res.index[0]
            row = st.session_state.df.loc[idx]
            
            # ID Card & QR Logic
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={row['Ticket_Number']}"
            st.markdown(f"""
                <div class="id-card">
                    <div class="id-role">{row['Role']}</div>
                    <h2>{row['Name']}</h2>
                    <p>🎟 Ticket: {row['Ticket_Number']} | 📞 Spot: {row['Spot Phone']}</p>
                    <p>👨‍👩‍👦 Guardian: {row['Guardian Phone']}</p>
                    <img src="{qr_url}" width="120">
                    <div style="margin-top:10px;">{'✅ ENTERED' if row['Entry_Status']=='Done' else '⏳ PENDING'}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Actions
            with st.form("action"):
                c1, c2, c3 = st.columns(3)
                ent = c1.checkbox("Entry", value=(row['Entry_Status']=='Done'))
                kit = c2.checkbox("Kit", value=(row['T_Shirt_Collected']=='Yes'))
                food = c3.checkbox("Food", value=(row.get('Food_Collected','')=='Yes'))
                if st.form_submit_button("Update Status"):
                    st.session_state.df.at[idx, 'Entry_Status'] = 'Done' if ent else ''
                    st.session_state.df.at[idx, 'T_Shirt_Collected'] = 'Yes' if kit else 'No'
                    st.session_state.df.at[idx, 'Food_Collected'] = 'Yes' if food else 'No'
                    conn.update(worksheet="Data", data=st.session_state.df)
                    st.success("Updated!")
                    st.rerun()

elif menu == "🚌 Bus Fleet":
    st.title("🚌 Fleet Manager")
    bus_names = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    cols = st.columns(4)
    for i, b in enumerate(bus_names):
        count = len(st.session_state.df[st.session_state.df['Bus_Number'] == b])
        cols[i].metric(b, f"{count}/{BUS_CAPACITY}", delta=f"{BUS_CAPACITY-count} left")
    
    # Export Printable HTML
    if st.button("📄 Generate Printable Manifest"):
        html = "<html><body style='font-family:sans-serif;'><h1>Bus Manifest</h1>"
        for b in bus_names:
            b_df = st.session_state.df[st.session_state.df['Bus_Number'] == b]
            if not b_df.empty:
                html += f"<h2>{b}</h2><table border='1' width='100%'><tr><th>Sl.</th><th>Name</th><th>Class</th><th>Ticket</th><th>In Sign</th><th>Out Sign</th></tr>"
                for j, (_, r) in enumerate(b_df.iterrows(), 1):
                    html += f"<tr><td>{j}</td><td>{r['Name']}</td><td>{r['Class']}</td><td>{r['Ticket_Number']}</td><td></td><td></td></tr>"
                html += "</table>"
        html += "</body></html>"
        st.download_button("Download Manifest", html, "Manifest.html", "text/html")
