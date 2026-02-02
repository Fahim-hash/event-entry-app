import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time
import pytz
import streamlit.components.v1 as components

# ==================== 1. CONFIG & STYLE (THEMED BACKGROUND) ====================
st.set_page_config(page_title="Event OS Pro", page_icon="🎆", layout="wide")

st.markdown("""
    <style>
    /* 🔥 FULL PAGE BACKGROUND WITH FADED DJ THEME 🔥 */
    .stApp {
        background-color: #000000; /* Fallback */
        
        /* Dark Overlay (0.85) + DJ Image */
        background-image: 
            linear-gradient(rgba(0, 0, 0, 0.85), rgba(0, 0, 0, 0.9)),
            url("https://images.unsplash.com/photo-1470225620780-dba8ba36b745?q=80&w=2070&auto=format&fit=crop");
            
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: #ffffff;
    }
    
    /* SIDEBAR - Semi-Transparent Dark */
    section[data-testid="stSidebar"] {
        background-color: rgba(10, 10, 10, 0.9);
        border-right: 1px solid #333;
    }
    
    /* METRICS BOX - Glassmorphism */
    div[data-testid="stMetric"] {
        background-color: rgba(20, 20, 20, 0.7); /* Transparent */
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-left: 5px solid #d500f9;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    div[data-testid="stMetricLabel"] { color: #dcdcdc !important; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; text-shadow: 0 0 10px #d500f9; }
    
    /* === ID CARD STYLES (PREMIUM) === */
    
    /* 1. STUDENT (Modern Blue) */
    .card-student {
        background: linear-gradient(145deg, rgba(15, 32, 39, 0.9), rgba(44, 83, 100, 0.9));
        backdrop-filter: blur(5px);
        border: 1px solid #4ca1af;
        box-shadow: 0 4px 15px rgba(76, 161, 175, 0.3);
        border-radius: 15px; padding: 20px; text-align: center; margin-bottom: 20px;
    }

    /* 2. ORGANIZER (Neon Purple) */
    .card-organizer {
        background: linear-gradient(135deg, rgba(58, 0, 136, 0.9), rgba(114, 9, 183, 0.9));
        border: 2px solid #f72585;
        box-shadow: 0 0 20px rgba(247, 37, 133, 0.6);
        border-radius: 15px; padding: 20px; text-align: center; margin-bottom: 20px;
    }

    /* 3. TEACHER / STAFF (Teal) */
    .card-staff {
        background: linear-gradient(145deg, rgba(17, 153, 142, 0.9), rgba(56, 239, 125, 0.9));
        border: 2px solid #ffffff;
        box-shadow: 0 4px 15px rgba(56, 239, 125, 0.4);
        border-radius: 15px; padding: 20px; text-align: center; margin-bottom: 20px;
        color: #000 !important;
    }
    .card-staff .id-name, .card-staff .info-row { color: #000 !important; font-weight: bold; }

    /* 4. VOLUNTEER (Orange) */
    .card-volunteer {
        background: linear-gradient(145deg, rgba(255, 65, 108, 0.9), rgba(255, 75, 43, 0.9));
        border: 1px solid #ff9966;
        box-shadow: 0 4px 15px rgba(255, 75, 43, 0.4);
        border-radius: 15px; padding: 20px; text-align: center; margin-bottom: 20px;
    }

    /* 5. ELITE (Gold) */
    .card-elite {
        background: radial-gradient(ellipse at center, #FFD700 0%, #B8860B 100%);
        border: 3px solid #FFF;
        box-shadow: 0 0 30px rgba(255, 215, 0, 0.6);
        border-radius: 15px; padding: 20px; text-align: center; margin-bottom: 20px;
        color: #000 !important;
    }
    .card-elite .id-name, .card-elite .info-row { color: #000 !important; font-weight: bold; }

    /* COMMON TEXT */
    .id-name { font-size: 26px; font-weight: bold; margin: 10px 0; color: white; }
    .info-row { display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.2); padding: 8px 0; font-size: 14px; }
    .role-badge { background: rgba(0,0,0,0.6); color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; border: 1px solid rgba(255,255,255,0.3); }
    
    /* INPUT FIELDS */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(0, 0, 0, 0.8);
        color: white;
        border: 1px solid #555;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== 2. DATA ENGINE ====================
conn = st.connection("gsheets", type=GSheetsConnection)
BUS_CAPACITY = 45

def load_data():
    try:
        df = conn.read(worksheet="Data", ttl=0)
        req_cols = ['Name', 'Role', 'Spot Phone', 'Guardian Phone', 'Ticket_Number', 'Class', 'Roll', 'Entry_Status', 'Entry_Time', 'Bus_Number', 'T_Shirt_Size', 'T_Shirt_Collected', 'Notes']
        for c in req_cols:
            if c not in df.columns: df[c] = ''
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True).replace(['nan', 'None', ''], 'N/A')
        return df
    except Exception as e:
        return pd.DataFrame()

def load_stock():
    try:
        df_s = conn.read(worksheet="Stock", ttl=0)
        stock = dict(zip(df_s['Size'], df_s['Quantity']))
        return {s: int(float(stock.get(s, 0))) for s in ["S", "M", "L", "XL", "XXL"]}
    except: return {"S":0, "M":0, "L":0, "XL":0, "XXL":0}

if 'df' not in st.session_state: st.session_state.df = load_data()
if 'stock' not in st.session_state: st.session_state.stock = load_stock()

# ==================== 3. LOGIN ====================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.title("🔐 Willian's 26 | Admin")
    c1, c2 = st.columns(2)
    with c1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login", type="primary"):
            if u == "admin" and p == "1234":
                st.session_state.logged_in = True; st.session_state.user = u; st.rerun()
            else: st.error("Wrong Password!")
    st.stop()

# ==================== 4. LIVE DIGITAL TIMER ====================
st.sidebar.title("⚡ Menu")
target_iso = "2026-02-03T07:00:00+06:00"

timer_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{ margin: 0; font-family: 'Courier New', monospace; background-color: transparent; }}
    .timer-container {{
        background: linear-gradient(135deg, #000428 0%, #004e92 100%);
        color: white;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.2);
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }}
    .label {{ font-family: sans-serif; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px; color: #00ff88; }}
    .time {{ font-size: 28px; font-weight: bold; letter-spacing: 1px; color: #fff; text-shadow: 0 0 10px #00ff88; }}
    .sub-labels {{ font-size: 10px; opacity: 0.6; margin-top: 2px; font-family: sans-serif; }}
</style>
</head>
<body>
    <div class="timer-container">
        <div class="label">EVENT COUNTDOWN</div>
        <div id="countdown" class="time">-- : -- : --</div>
        <div class="sub-labels">HOURS &nbsp;&nbsp; MIN &nbsp;&nbsp; SEC</div>
    </div>
<script>
function updateTimer() {{
    const target = new Date("{target_iso}").getTime();
    setInterval(function() {{
        const now = new Date().getTime();
        const diff = target - now;
        if (diff < 0) {{ document.getElementById("countdown").innerHTML = "STARTED!"; return; }}
        const totalHours = Math.floor(diff / (1000 * 60 * 60));
        const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const s = Math.floor((diff % (1000 * 60)) / 1000);
        const hh = totalHours < 10 ? "0" + totalHours : totalHours;
        const mm = m < 10 ? "0" + m : m;
        const ss = s < 10 ? "0" + s : s;
        document.getElementById("countdown").innerHTML = hh + " : " + mm + " : " + ss;
    }}, 1000);
}}
updateTimer();
</script>
</body>
</html>
"""
with st.sidebar: components.html(timer_html, height=130)

menu = st.sidebar.radio("Go To", ["🔍 Search & Entry", "➕ Add Staff/Teacher", "📜 View Lists", "🚫 Absent List", "🚌 Bus Manager", "📊 Dashboard", "📝 Admin Data"])

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear(); st.session_state.df = load_data(); st.session_state.stock = load_stock(); st.rerun()

# --- TAB: SEARCH & ENTRY ---
if menu == "🔍 Search & Entry":
    st.title("🔍 Search & Entry")
    q = st.text_input("🔎 Search by Ticket / Name / Phone:").strip()
    if q:
        df = st.session_state.df
        mask = df['Name'].str.contains(q, case=False, regex=False) | \
               df['Ticket_Number'].str.contains(q, case=False, regex=False) | \
               df['Spot Phone'].str.contains(q, case=False, regex=False)
        res = df[mask]
        
        if not res.empty:
            idx = res.index[0]
            row = df.loc[idx]
            
            # Card Style Logic
            role = row['Role']
            if role in ["Principal", "College Head"]: card_class = "card-elite"
            elif role == "Organizer": card_class = "card-organizer"
            elif role in ["Teacher", "College Staff"]: card_class = "card-staff"
            elif role == "Volunteer": card_class = "card-volunteer"
            else: card_class = "card-student"

            is_ent = row['Entry_Status'] == 'Done'
            is_kit = row['T_Shirt_Collected'] == 'Yes'
            sz = row['T_Shirt_Size']
            rem = st.session_state.stock.get(sz, 0)
            
            col1, col2 = st.columns([1, 1.5])
            with col1:
                status_color = "#00ff88" if is_ent else "#ff4b4b"
                st.markdown(f"""
                <div class="{card_class}">
                    <div style="background:{status_color}; color:black; font-weight:bold; padding:5px; border-radius:5px; margin-bottom:10px;">
                        {'✅ CHECKED IN' if is_ent else '⏳ NOT ENTERED'}
                    </div>
                    <span class="role-badge">{row['Role']}</span>
                    <div class="id-name">{row['Name']}</div>
                    <div class="info-row"><span>Ticket:</span> <b>{row['Ticket_Number']}</b></div>
                    <div class="info-row"><span>Bus:</span> <b>{row['Bus_Number']}</b></div>
                    <div style="margin-top:10px; border:1px solid rgba(255,255,255,0.3); padding:8px; border-radius:8px;">
                        👕 Size: <b>{sz}</b> | Status: {'✅ GIVEN' if is_kit else f'📦 {rem} Left'}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if row['Bus_Number'] != "Unassigned":
                    if st.button(f"❌ Unassign {row['Bus_Number']}", type="secondary", key=f"un_{idx}"):
                        st.session_state.df.at[idx, 'Bus_Number'] = 'Unassigned'
                        conn.update(worksheet="Data", data=st.session_state.df)
                        st.success(f"Removed from {row['Bus_Number']}!"); time.sleep(0.5); st.rerun()

            with col2:
                with st.container(border=True):
                    st.subheader("✏️ Update Details")
                    c_n, c_r = st.columns([1.5, 1])
                    new_name = c_n.text_input("Name", row['Name'])
                    role_opts = ["Student", "Volunteer", "Teacher", "College Staff", "Organizer", "Principal", "College Head"]
                    new_role = c_r.selectbox("Role", role_opts, index=role_opts.index(row['Role']) if row['Role'] in role_opts else 0)
                    c_p, c_t = st.columns(2)
                    new_phone = c_p.text_input("Phone", row['Spot Phone'])
                    new_ticket = c_t.text_input("Ticket", row['Ticket_Number'])
                    new_size = st.selectbox("Size", ["S", "M", "L", "XL", "XXL"], index=["S", "M", "L", "XL", "XXL"].index(sz) if sz in ["S", "M", "L", "XL", "XXL"] else 2)
                    st.markdown("---")
                    c_a, c_b = st.columns(2)
                    new_ent = c_a.toggle("✅ Entry", is_ent)
                    new_kit = c_b.toggle("👕 Kit", is_kit)
                    buses = ["Unassigned", "Bus 1", "Bus 2", "Bus 3", "Bus 4"]
                    new_bus = st.selectbox("🚌 Bus", buses, index=buses.index(row['Bus_Number']) if row['Bus_Number'] in buses else 0)
                    
                    if st.button("💾 Save Changes", type="primary"):
                        if not new_phone or new_phone=='N/A': st.error("Phone Required!")
                        else:
                            can_assign = True
                            if new_bus != "Unassigned" and new_bus != row['Bus_Number']:
                                if len(df[df['Bus_Number'] == new_bus]) >= BUS_CAPACITY: st.error("Bus Full!"); can_assign = False
                            if can_assign:
                                if new_kit:
                                    if is_kit and sz != new_size: st.session_state.stock[sz]+=1; st.session_state.stock[new_size]-=1
                                    elif not is_kit: st.session_state.stock[new_size]-=1
                                elif not new_kit and is_kit: st.session_state.stock[sz]+=1
                                st.session_state.df.at[idx, 'Name'] = new_name
                                st.session_state.df.at[idx, 'Role'] = new_role
                                st.session_state.df.at[idx, 'Spot Phone'] = new_phone
                                st.session_state.df.at[idx, 'Ticket_Number'] = new_ticket
                                st.session_state.df.at[idx, 'T_Shirt_Size'] = new_size
                                st.session_state.df.at[idx, 'Entry_Status'] = 'Done' if new_ent else 'N/A'
                                st.session_state.df.at[idx, 'T_Shirt_Collected'] = 'Yes' if new_kit else 'No'
                                st.session_state.df.at[idx, 'Bus_Number'] = new_bus
                                if new_ent and row['Entry_Time'] == 'N/A': st.session_state.df.at[idx, 'Entry_Time'] = datetime.now().strftime("%H:%M:%S")
                                conn.update(worksheet="Data", data=st.session_state.df)
                                s_d = [{"Size": k, "Quantity": v} for k, v in st.session_state.stock.items()]
                                conn.update(worksheet="Stock", data=pd.DataFrame(s_d))
                                st.success("Updated!"); time.sleep(0.5); st.rerun()
        else: st.warning("Not Found")

# --- TAB: ADD STAFF ---
elif menu == "➕ Add Staff/Teacher":
    st.title("➕ Add Manual Entry")
    with st.form("add"):
        c1, c2 = st.columns(2); name = c1.text_input("Name"); ph = c2.text_input("Phone")
        c3, c4 = st.columns(2); role = c3.selectbox("Role", ["Teacher", "College Staff", "Guest", "Volunteer", "Principal", "College Head"]); cls = c4.text_input("Class", "N/A")
        if st.form_submit_button("Add"):
            if name and ph:
                new = {'Name':name, 'Role':role, 'Spot Phone':ph, 'Ticket_Number':f"MAN-{int(time.time())}", 'Class':cls, 'Roll':'N/A', 'Entry_Status':'N/A', 'Entry_Time':'N/A', 'Bus_Number':'Unassigned', 'T_Shirt_Size':'L', 'T_Shirt_Collected':'No', 'Notes':'Manual'}
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new])], ignore_index=True)
                conn.update(worksheet="Data", data=st.session_state.df); st.success("Added!"); time.sleep(1); st.rerun()

# --- TAB: VIEW LISTS ---
elif menu == "📜 View Lists":
    st.title("📜 View Lists")
    filter_type = st.radio("Filter By:", ["Class", "Role"], horizontal=True)
    view_df = pd.DataFrame()
    if filter_type == "Class":
        cls_list = sorted([c for c in st.session_state.df['Class'].unique() if c not in ['', 'N/A']])
        sel = st.selectbox("Select Class", ["All"] + cls_list)
        view_df = st.session_state.df if sel == "All" else st.session_state.df[st.session_state.df['Class'] == sel]
    else:
        role_list = sorted([r for r in st.session_state.df['Role'].unique() if r not in ['', 'N/A']])
        sel_role = st.selectbox("Select Role", ["All"] + role_list)
        view_df = st.session_state.df if sel_role == "All" else st.session_state.df[st.session_state.df['Role'] == sel_role]
    c1, c2, c3 = st.columns(3)
    c1.metric("Total", len(view_df)); c2.metric("Checked In", len(view_df[view_df['Entry_Status']=='Done'])); c3.metric("Pending", len(view_df)-len(view_df[view_df['Entry_Status']=='Done']))
    st.dataframe(view_df[['Name', 'Role', 'Class', 'Spot Phone', 'Entry_Status']], use_container_width=True)

# --- TAB: ABSENT LIST ---
elif menu == "🚫 Absent List":
    st.title("🚫 Absentee Manager")
    abs_df = st.session_state.df[st.session_state.df['Entry_Status'] != 'Done']
    c1, c2 = st.columns(2); c1.metric("Total Absent", len(abs_df)); c2.metric("Registered", len(st.session_state.df))
    cls_list = sorted([c for c in abs_df['Class'].unique() if c not in ['', 'N/A']])
    sel = st.selectbox("Filter Class", ["All"] + cls_list)
    v_abs = abs_df if sel == "All" else abs_df[abs_df['Class'] == sel]
    st.dataframe(v_abs[['Name', 'Class', 'Role', 'Spot Phone']], use_container_width=True)
    if st.button("🖨️ Print Absent List"):
        html = f"<html><body><h1>Absent List - {sel}</h1><table><tr><th>Name</th><th>Class</th><th>Phone</th></tr>"
        for _, r in v_abs.iterrows(): html += f"<tr><td>{r['Name']}</td><td>{r['Class']}</td><td>{r['Spot Phone']}</td></tr>"
        html += "</table></body></html>"
        st.download_button("⬇️ PDF Ready", html, "Absent.html", "text/html")

# --- TAB: BUS MANAGER ---
elif menu == "🚌 Bus Manager":
    st.title("🚌 Fleet Manager")
    buses = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    cols = st.columns(4)
    for i, b in enumerate(buses):
        df_b = st.session_state.df[st.session_state.df['Bus_Number'] == b]
        cnt = len(df_b)
        cols[i].metric(b, f"{cnt}/{BUS_CAPACITY}", f"{BUS_CAPACITY-cnt} Free"); cols[i].progress(min(cnt/BUS_CAPACITY, 1.0))
    st.markdown("---")
    
    with st.expander("🗑️ Bulk Unassign Tools"):
        st.subheader("Option: Empty a Bus")
        target_bus = st.selectbox("Select Bus to Empty:", buses)
        if st.button(f"🗑️ Empty {target_bus}"): 
             mask = st.session_state.df['Bus_Number'] == target_bus
             if mask.sum() > 0:
                 st.session_state.df.loc[mask, 'Bus_Number']='Unassigned'
                 conn.update(worksheet="Data", data=st.session_state.df)
                 st.success(f"Emptied {target_bus}!"); time.sleep(1); st.rerun()
             else: st.warning("Bus is already empty.")

    st.subheader("🖨️ Print Manifest")
    if st.button("📄 Generate PDF Ready"):
        html = "<html><head><style>@page{size:A4;margin:10mm;} body{font-family:Arial;font-size:12px;} table{width:100%;border-collapse:collapse;} th,td{border:1px solid black;padding:5px;} .page{page-break-after:always;}</style></head><body>"
        for b in buses:
            b_df = st.session_state.df[st.session_state.df['Bus_Number'] == b]
            if not b_df.empty:
                html += f"<div class='page'><h1>{b} List ({len(b_df)})</h1><table><tr><th>SL</th><th>Name</th><th>Role</th><th>Phone</th><th>Sign</th></tr>"
                for i, (_, r) in enumerate(b_df.iterrows(), 1): html += f"<tr><td>{i}</td><td>{r['Name']}</td><td>{r['Role']}</td><td>{r['Spot Phone']}</td><td></td></tr>"
                html += "</table></div>"
        html += "</body></html>"
        st.download_button("⬇️ Download", html, "Manifest.html", "text/html")

    st.subheader("🚀 Auto Assign")
    c1, c2 = st.columns(2); role = c1.selectbox("Role", ["Student", "Volunteer", "Teacher"]); start = c2.selectbox("Start", buses)
    if st.button("Assign"):
        mask = st.session_state.df['Role'] == role; idxs = st.session_state.df[mask].index
        b_i = buses.index(start); cnt=0
        for i in idxs:
            while b_i<4:
                if len(st.session_state.df[st.session_state.df['Bus_Number']==buses[b_i]]) < BUS_CAPACITY:
                    st.session_state.df.at[i, 'Bus_Number'] = buses[b_i]; cnt+=1; break
                else: b_i+=1
        conn.update(worksheet="Data", data=st.session_state.df); st.success(f"Assigned {cnt}!"); st.rerun()

# --- TAB: DASHBOARD ---
elif menu == "📊 Dashboard":
    st.title("📊 Event Stats")
    
    if not st.session_state.df.empty:
        df = st.session_state.df
        grp1 = ['Student', 'Organizer', 'Volunteer']
        cnt1 = len(df[df['Role'].isin(grp1)])
        grp2 = ['Teacher', 'College Staff', 'Principal', 'College Head']
        cnt2 = len(df[df['Role'].isin(grp2)])
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Registered", len(df))
        c2.metric("Students + Team", cnt1)
        c3.metric("Faculty & Staff", cnt2)
        c4.metric("Checked In", len(df[df['Entry_Status']=='Done']))
        st.markdown("### T-Shirt Distribution")
        st.bar_chart(df['T_Shirt_Size'].value_counts())
    else:
        st.warning("⚠️ No data available.")

# --- TAB: ADMIN DATA ---
elif menu == "📝 Admin Data":
    st.title("📝 Full DB"); st.dataframe(st.session_state.df)
    st.download_button("Download CSV", st.session_state.df.to_csv(), "data.csv")
