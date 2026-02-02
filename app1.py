import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import time
from datetime import datetime

# ১. কনফিগারেশন
st.set_page_config(page_title="Event OS Pro", layout="wide")

# ২. কানেকশন এবং ডাটা লোড
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_update(ws, data):
    try:
        conn.update(worksheet=ws, data=data)
        return True
    except Exception as e:
        st.error(f"Error updating: {e}")
        return False

def load_data():
    try:
        df = conn.read(worksheet="Data", ttl=0)
        return df.fillna("N/A")
    except:
        return pd.DataFrame()

if 'df' not in st.session_state:
    st.session_state.df = load_data()

# ৩. সাইডবার মেনু (এই 'menu' ভেরিয়েবলটি নিচে ব্যবহার করা হয়েছে)
st.sidebar.title("⚡ Navigation")
menu = st.sidebar.radio("Go To", ["🔍 Search & Entry", "🚌 Bus Manager", "📝 Admin Data"])

# ৪. বাস ম্যানেজার সেকশন (এখানেই আপনার এরর ছিল)
if menu == "🚌 Bus Manager":
    st.title("🚌 Fleet & Visual Layout")
    
    buses = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    BUS_CAPACITY = 45 
    
    st.subheader("📍 Real-time Occupancy Visual")
    cols = st.columns(4)
    
    for i, b in enumerate(buses):
        df_b = st.session_state.df[st.session_state.df['Bus_Number'] == b]
        cnt = len(df_b)
        with cols[i]:
            st.metric(b, f"{cnt}/{BUS_CAPACITY}")
            
            # বাসের সিট প্ল্যান ভিজ্যুয়াল
            # 
            grid_html = ""
            for s in range(BUS_CAPACITY):
                grid_html += "🔵" if s < cnt else "⚪"
                if (s+1) % 4 == 0: grid_html += "<br>" 
            
            st.markdown(f"<div style='font-size:12px; line-height:1.2;'>{grid_html}</div>", unsafe_allow_html=True)
            st.progress(min(cnt/BUS_CAPACITY, 1.0))

    st.markdown("---")
    
    # র‍্যান্ডম অ্যাসাইনমেন্ট
    st.subheader("🎲 Random Lucky Seating")
    role_to_assign = st.selectbox("Assign Role", ["Student", "Volunteer", "Teacher"])
    
    if st.button("🚀 Start Random Assignment"):
        unassigned = st.session_state.df[(st.session_state.df['Role'] == role_to_assign) & (st.session_state.df['Bus_Number'] == 'Unassigned')].index.tolist()
        
        if not unassigned:
            st.warning("No one left to assign!")
        else:
            import random
            random.shuffle(unassigned) # লটারি করার জন্য র‍্যান্ডম করা হলো
            
            assigned_count = 0
            for b in buses:
                current_count = len(st.session_state.df[st.session_state.df['Bus_Number'] == b])
                free = BUS_CAPACITY - current_count
                while free > 0 and unassigned:
                    idx = unassigned.pop()
                    st.session_state.df.at[idx, 'Bus_Number'] = b
                    free -= 1
                    assigned_count += 1
            
            if safe_update("Data", st.session_state.df):
                st.success(f"Assigned {assigned_count} people randomly!")
                st.rerun()

# ৫. অন্যান্য মেনু
elif menu == "🔍 Search & Entry":
    st.title("🔍 Search")
    st.write("Search features here...")

elif menu == "📝 Admin Data":
    st.title("📝 Data View")
    st.dataframe(st.session_state.df)
