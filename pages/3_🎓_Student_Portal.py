import streamlit as st
import utils
from datetime import datetime

utils.init_page("Student Portal")

# সিকিউরিটি চেক: লগইন ছাড়া কেউ লিংক দিয়ে ঢুকতে পারবে না
if 'portal_user' not in st.session_state or not st.session_state.portal_user:
    st.error("🔒 Access Denied! Please Login from Home Page.")
    if st.button("Go to Login"):
        st.switch_page("Home.py")
    st.stop()

# ডাটা লোড
tid = st.session_state.portal_user
df = st.session_state.df
user_row = df[df['Ticket_Number'] == tid].iloc[0]

st.title(f"👋 Welcome, {user_row['Name']}")

tab1, tab2, tab3 = st.tabs(["🆔 Digital Pass", "🚩 Report Fault", "📞 Contacts"])

# --- TAB 1: DIGITAL ID ---
with tab1:
    st.markdown(f"""
    <div class="id-card">
        <h3 style="margin:0; color:#00d2ff;">OFFICIAL STUDENT PASS</h3>
        <h1 style="margin:10px 0; font-size:2rem;">{user_row['Name']}</h1>
        <p style="font-size:1.2rem;">🎫 Ticket: <b>{user_row['Ticket_Number']}</b></p>
        <p>🚌 Bus: <b>{user_row['Bus_Number']}</b></p>
        <div style="margin-top:15px; padding:8px; background:{'#00ff88' if user_row['Entry_Status']=='Done' else '#ff4b4b'}; color:black; font-weight:bold; border-radius:5px;">
            STATUS: {'CHECKED-IN' if user_row['Entry_Status']=='Done' else 'NOT ENTERED'}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- TAB 2: FAULT REPORT ---
with tab2:
    st.subheader("Submit a Complaint")
    with st.form("fault_form"):
        issue = st.text_area("What issue are you facing?", placeholder="E.g. Wrong bus assigned, Name spelling mistake...")
        # Image Upload (Optional)
        img = st.file_uploader("Upload Screenshot (Optional)", type=['png', 'jpg'])
        
        if st.form_submit_button("Submit Report", type="primary"):
            # Update Database
            idx = df[df['Ticket_Number'] == tid].index[0]
            st.session_state.df.at[idx, 'Fault_Report'] = issue
            utils.get_conn().update(worksheet="Data", data=st.session_state.df)
            st.success("Report sent to Admins successfully!")

# --- TAB 3: CONTACTS ---
with tab3:
    st.subheader("Emergency Contacts")
    st.info("📞 **Admin Hotline:** 01XXXXXXXXX")
    st.info("🚌 **Transport Lead:** 01XXXXXXXXX")

# Logout
if st.sidebar.button("🚪 Logout Portal"):
    st.session_state.portal_user = None
    st.switch_page("Home.py")
