import streamlit as st
import utils

utils.init_page("Home | Event OS")
utils.init_session()

st.title("⚡ Event OS Ultimate")
t1, t2 = st.tabs(["🔐 Staff Login", "🎓 Student Portal"])

with t1:
    with st.form("staff"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            CREDS = {"admin": "1234", "gate": "entry26"}
            if u in CREDS and CREDS[u] == p:
                st.session_state.logged_in = True
                st.session_state.user_role = "admin" if u=="admin" else "gate"
                st.session_state.user_name = u
                st.session_state.df = utils.load_data()
                st.session_state.stock = utils.load_stock()
                st.success("Success! Go to Access Terminal page.")
                st.rerun()
            else: st.error("Wrong Password")

with t2:
    with st.form("student"):
        tid = st.text_input("Ticket Number")
        phone = st.text_input("Spot Phone", type="password")
        if st.form_submit_button("Enter Portal"):
            df = utils.load_data()
            match = df[(df['Ticket_Number'] == tid) & (df['Spot Phone'] == phone)]
            if not match.empty:
                st.session_state.portal_user = tid
                st.session_state.df = df
                st.switch_page("pages/3_🎓_Student_Portal.py")
            else: st.error("Record Not Found")
