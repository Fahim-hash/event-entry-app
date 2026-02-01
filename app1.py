import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time
import pytz

# ==================== 1. CONFIG & STYLE ====================
st.set_page_config(page_title="Event OS Pro", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #e0e0e0; }
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px; padding: 10px;
    }
    .id-card {
        background: linear-gradient(135deg, #121212 0%, #1e1e1e 100%);
        border: 2px solid #333; border-radius: 15px; padding: 20px;
        text-align: center; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .id-name { font-size: 26px; font-weight: bold; margin: 10px 0; color: white; }
    .role-badge { background: #FFD700; color: black; padding: 2px 10px; border-radius: 10px; font-weight: bold; font-size: 12px; }
    input[type="text"] {
        border: 1px solid #444 !important; background-color: #1a1a1a !important; color: white !important;
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
    except: return pd.DataFrame()

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
    st.title("🔐 Admin Login")
    c1, c2 = st.columns(2)
    with c1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login", type="primary"):
            if u == "admin" and p == "1234":
                st.session_state.logged_in = True; st.session_state.user = u; st.rerun()
            else: st.error("Wrong Password!")
    st.stop()

# ==================== 4. LIVE JS TIMER ====================
st.sidebar.title("⚡ Menu")

# JavaScript Timer (No Refresh Needed)
# Target: Feb 3, 2026 07:00:00 GMT+6
target_iso = "2026-02-03T07:00:00+06:00"

st.sidebar.markdown(f"""
<div style="background: linear-gradient(45deg, #ff00cc, #333399); padding: 15px; border-radius: 12px; text-align: center; color: white; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.2);">
    <h4 style="margin:0; font-size: 13px; opacity: 0.8; text-transform: uppercase; letter-spacing: 1px;">🚀 Event Starts In</h4>
    <div id="countdown" style="font-size: 22px; font-weight: 900; margin: 8px 0; text-shadow: 0 0 10px rgba(255,255,255,0.5); font-family: monospace;">
        Loading...
    </div>
    <small style="opacity: 0.7;">3rd Feb 2026, 7:00 AM</small>
</div>

<script>
function updateTimer() {{
    const target = new Date("{target_iso}").getTime();
    const now = new Date().getTime();
    const diff = target - now;

    if (diff < 0) {{
        document.getElementById("countdown").innerHTML = "EVENT STARTED!";
        return;
    }}

    const d = Math.floor(diff / (1000 * 60 * 60 * 24));
    const h = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const s = Math.floor((diff % (1000 * 60)) / 1000);

    // Format with leading zeros
    const hh = h < 10 ? "0" + h : h;
    const mm = m < 10 ? "0" + m : m;
    const ss = s < 10 ? "0" + s : s;

    document.getElementById("countdown").innerHTML = d + "d : " + hh + "h : " + mm + "m : " + ss + "s";
}}
setInterval(updateTimer, 1000);
updateTimer();
</script>
""", unsafe_allow_html=True)

menu = st.sidebar.radio("Go To", ["🔍 Search & Entry", "➕ Add Staff/Teacher", "📜 View Lists (Student/Staff)", "🚫 Absent List", "🚌 Bus Manager", "📊 Dashboard", "📝 Admin Data"])

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear(); st.session_state.df = load_data(); st.session_state.stock = load_stock(); st.rerun()

# --- TAB 1: SEARCH & ENTRY ---
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
            
            is_ent = row['Entry_Status'] == 'Done'
            is_kit = row['T_Shirt_Collected'] == 'Yes'
            sz = row['T_Shirt_Size']
            rem = st.session_state.stock.get(sz, 0)
            
            if not is_kit and rem <= 5: st.warning(f"⚠️ LOW STOCK: {sz} ({rem} left)")

            col1, col2 = st.columns([1, 1.5])
            with col1:
                border_c = "#00ff88" if is_ent else "#ff4b4b"
                st.markdown(f"""
                <div class="id-card" style="border: 2px solid {border_c};">
                    <div style="background:{border_c}; color:black; font-weight:bold; padding:5px; border-radius:5px;">{'✅ CHECKED IN' if is_ent else '⏳ NOT ENTERED'}</div>
                    <br><span class="role-badge">{row['Role']}</span>
                    <div class="id-name">{row['Name']}</div>
                    <div class="info-row"><span>Ticket:</span> <b>{row['Ticket_Number']}</b></div>
                    <div class="info-row"><span>Bus:</span> <b>{row['Bus_Number']}</b></div>
                    <div style="margin-top:10px; border:1px solid #555; padding:8px; border-radius:8px;">
                        👕 Size: <b>{sz}</b> | Status: {'✅ GIVEN' if is_kit else f'📦 {rem} Left'}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 🔥 FIXED INDIVIDUAL UNASSIGN 🔥
                if row['Bus_Number'] != "Unassigned":
                    # Added unique key to prevent conflict
                    if st.button(f"❌ Unassign {row['Bus_Number']}", type="secondary", key=f"un_{idx}"):
                        st.session_state.df.at[idx, 'Bus_Number'] = 'Unassigned'
                        conn.update(worksheet="Data", data=st.session_state.df)
                        st.success(f"Removed from {row['Bus_Number']}!")
                        time.sleep(0.5); st.rerun()

            with col2:
                with st.container(border=True):
                    st.subheader("✏️ Edit & Actions")
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
                        if not new_phone or new_phone=='N/A' or not new_ticket or new_ticket=='N/A': st.error("Phone & Ticket Required!")
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
        c3, c4 = st.columns(2)
        role = c3.selectbox("Role", ["Teacher", "College Staff", "Guest", "Volunteer", "Principal", "College Head"])
        cls = c4.text_input("Class (Optional)", "N/A")
        if st.form_submit_button("Add"):
            if name and ph:
                new = {'Name':name, 'Role':role, 'Spot Phone':ph, 'Ticket_Number':f"MAN-{int(time.time())}", 'Class':cls, 'Roll':'N/A', 'Entry_Status':'N/A', 'Entry_Time':'N/A', 'Bus_Number':'Unassigned', 'T_Shirt_Size':'L', 'T_Shirt_Collected':'No', 'Notes':'Manual'}
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new])], ignore_index=True)
                conn.update(worksheet="Data", data=st.session_state.df); st.success("Added!"); time.sleep(1); st.rerun()

# --- TAB: VIEW LISTS ---
elif menu == "📜 View Lists (Student/Staff)":
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
    c1.metric("Total Found", len(view_df))
    c2.metric("Checked In", len(view_df[view_df['Entry_Status']=='Done']))
    c3.metric("Pending", len(view_df)-len(view_df[view_df['Entry_Status']=='Done']))
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
        # 🔥 FIXED BULK UNASSIGN DROPDOWN 🔥
        st.subheader("Option: Empty a Bus")
        target_bus = st.selectbox("Select Bus to Empty:", buses)
        if st.button(f"🗑️ Empty {target_bus}"): 
             mask = st.session_state.df['Bus_Number'] == target_bus
             if mask.sum() > 0:
                 st.session_state.df.loc[mask, 'Bus_Number']='Unassigned'
                 conn.update(worksheet="Data", data=st.session_state.df)
                 st.success(f"Emptied {target_bus}!"); time.sleep(1); st.rerun()
             else:
                 st.warning("Bus is already empty.")

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

# --- TAB: ADMIN DATA ---
elif menu == "📝 Admin Data":
    st.title("📝 Full DB"); st.dataframe(st.session_state.df)
    st.download_button("Download CSV", st.session_state.df.to_csv(), "data.csv")
