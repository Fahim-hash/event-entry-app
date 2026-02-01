import streamlit as st
import utils
from datetime import datetime
import time

utils.init_page("Access Terminal")
utils.init_session()

if not st.session_state.get('logged_in'):
    st.error("🔒 Please Login from Home Page")
    st.stop()

st.title("🔍 Access Terminal")
q = st.text_input("Scan Ticket / Name / Phone:")

if q:
    df = st.session_state.df
    res = df[df['Name'].str.contains(q, case=False) | df['Ticket_Number'].str.contains(q, case=False)]
    
    if not res.empty:
        idx = res.index[0]
        row = df.loc[idx]
        
        is_ent = row['Entry_Status'] == 'Done'
        col = "#00ff88" if is_ent else "#ff4b4b"
        
        # HTML Rendering Fix (unsafe_allow_html=True নিশ্চিত করা হয়েছে)
        st.markdown(f"""
        <div class="id-card" style="border: 2px solid {col}">
            <h3 style="background:{col}; color:black; padding:5px; border-radius:5px;">{'✅ VERIFIED' if is_ent else '⛔ PENDING'}</h3>
            <h2>{row['Name']}</h2>
            <p>🎫 {row['Ticket_Number']} | 🚌 {row['Bus_Number']}</p>
            <p>👕 Size: {row['T_Shirt_Size']} | 📦 Given: {row['T_Shirt_Collected']}</p>
            <div class="notes-box">📝 Notes: {row['Notes']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Mark Entry"):
            st.session_state.df.at[idx, 'Entry_Status'] = 'Done'
            st.session_state.df.at[idx, 'Entry_Time'] = datetime.now().strftime("%H:%M:%S")
            utils.get_conn().update(worksheet="Data", data=st.session_state.df)
            utils.add_log(f"Entry: {row['Name']}")
            st.rerun()
            
        if c2.button("👕 Give Kit"):
            st.session_state.df.at[idx, 'T_Shirt_Collected'] = 'Yes'
            # Stock update logic here if needed
            utils.get_conn().update(worksheet="Data", data=st.session_state.df)
            st.rerun()
            
    else: st.warning("Not Found")
