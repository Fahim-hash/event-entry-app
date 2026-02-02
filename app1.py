# --- TAB: BUS MANAGER ---
elif menu == "🚌 Bus Manager":
    st.title("🚌 Fleet & Visual Layout")
    
    buses = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
    
    # --- 1. VISUAL BUS LAYOUT ---
    st.subheader("📍 Real-time Occupancy Visual")
    cols = st.columns(4)
    
    for i, b in enumerate(buses):
        df_b = st.session_state.df[st.session_state.df['Bus_Number'] == b]
        cnt = len(df_b)
        with cols[i]:
            st.metric(b, f"{cnt}/{BUS_CAPACITY}")
            # একটি ছোট ভিজ্যুয়াল গ্রিড (বাসের ভেতরটা কেমন দেখাবে)
            # খালি সিট = ⚪, বুকড সিট = 🔵
            grid = ""
            for s in range(BUS_CAPACITY):
                grid += "🔵" if s < cnt else "⚪"
                if (s+1) % 4 == 0: grid += "\n" # প্রতি ৪ সিট পর পর নতুন লাইন
            
            st.text(f"Interior View:\n{grid}")
            st.progress(min(cnt/BUS_CAPACITY, 1.0))

    st.markdown("---")
    
    # --- 2. RANDOM AUTO ASSIGN ---
    st.subheader("🎲 Random Lucky Seating (Auto Assign)")
    st.write("এটি বাসের খালি সিটগুলোতে স্টুডেন্টদের র‍্যান্ডমভাবে বসিয়ে দিবে।")
    
    c1, c2 = st.columns(2)
    role_to_assign = c1.selectbox("Assign which Role?", ["Student", "Volunteer", "Teacher"])
    
    if st.button("🚀 Start Random Assignment"):
        # যারা এখনো Unassigned আছে তাদের খুঁজে বের করা
        unassigned_mask = (st.session_state.df['Role'] == role_to_assign) & (st.session_state.df['Bus_Number'] == 'Unassigned')
        unassigned_indices = st.session_state.df[unassigned_mask].index.tolist()
        
        if not unassigned_indices:
            st.warning(f"No unassigned {role_to_assign} found!")
        else:
            import random
            random.shuffle(unassigned_indices) # ডাটা র‍্যান্ডম করা হলো
            
            total_assigned = 0
            for b in buses:
                # বর্তমানে বাসে কতজন আছে দেখা
                current_bus_count = len(st.session_state.df[st.session_state.df['Bus_Number'] == b])
                free_seats = BUS_CAPACITY - current_bus_count
                
                # যদি সিট খালি থাকে, র‍্যান্ডম মানুষ ঢোকানো শুরু হবে
                while free_seats > 0 and unassigned_indices:
                    idx = unassigned_indices.pop()
                    st.session_state.df.at[idx, 'Bus_Number'] = b
                    free_seats -= 1
                    total_assigned += 1
            
            if safe_update("Data", st.session_state.df):
                st.success(f"Successfully assigned {total_assigned} {role_to_assign}s randomly across buses!")
                time.sleep(1)
                st.rerun()

    # --- 3. PRINT MANIFEST ---
    st.markdown("---")
    st.subheader("🖨️ Get Manifest")
    if st.button("📄 Generate PDF Ready List"):
        html = "<html><head><style>body{font-family:sans-serif;} table{width:100%; border-collapse:collapse;} th,td{border:1px solid #ddd; padding:8px; text-align:left;} th{background:#f2f2f2;}</style></head><body>"
        for b in buses:
            b_df = st.session_state.df[st.session_state.df['Bus_Number'] == b]
            if not b_df.empty:
                html += f"<h2>{b} - Passenger List ({len(b_df)})</h2>"
                html += "<table><tr><th>Name</th><th>Phone</th><th>Class</th></tr>"
                for _, r in b_df.iterrows():
                    html += f"<tr><td>{r['Name']}</td><td>{r['Spot Phone']}</td><td>{r['Class']}</td></tr>"
                html += "</table><br>"
        html += "</body></html>"
        st.download_button("⬇️ Download Manifest", html, "Bus_Manifest.html", "text/html")
