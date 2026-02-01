import streamlit as st
import utils
import pandas as pd

utils.init_page("Transport Manager")
utils.check_auth() # শুধুমাত্র স্টাফরা দেখবে

st.title("🚌 Fleet Logistics")
buses = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
df = st.session_state.df

# --- BUS METRICS ---
cols = st.columns(4)
for i, b in enumerate(buses):
    count = len(df[df['Bus_Number'] == b])
    cols[i].metric(b, f"{count}/{utils.BUS_CAPACITY}", f"{utils.BUS_CAPACITY-count} Free")
    cols[i].progress(min(count/utils.BUS_CAPACITY, 1.0))

st.markdown("---")

# --- SMART AUTO ASSIGN ---
with st.expander("🚀 Smart Auto-Assign (Overflow Logic)", expanded=True):
    c1, c2, c3 = st.columns(3)
    mode = c1.selectbox("Filter By", ["Class", "Role"])
    # ড্রপডাউন অপশন ডায়নামিক লোড হবে
    opts = sorted(df[mode].unique()) if not df.empty else []
    val = c2.selectbox("Select Group", opts)
    start_bus = c3.selectbox("Start From", buses)
    
    if st.button("Start Assignment Sequence", type="primary"):
        indices = df[df[mode] == val].index.tolist()
        b_idx = buses.index(start_bus)
        assigned = 0
        
        for p_idx in indices:
            # বাস ফুল হলে পরের বাসে যাবে
            while b_idx < 4:
                curr_bus = buses[b_idx]
                curr_load = len(st.session_state.df[st.session_state.df['Bus_Number'] == curr_bus])
                
                if curr_load < utils.BUS_CAPACITY:
                    st.session_state.df.at[p_idx, 'Bus_Number'] = curr_bus
                    assigned += 1
                    break
                else:
                    b_idx += 1 # Next bus
        
        # ডাটাবেস আপডেট
        utils.get_conn().update(worksheet="Data", data=st.session_state.df)
        st.success(f"Logistics Updated! Assigned {assigned} people.")
        time.sleep(1)
        st.rerun()
