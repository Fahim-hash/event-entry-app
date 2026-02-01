import streamlit as st
import utils
import pandas as pd

utils.init_page("Admin Panel")
utils.check_auth("admin") # শুধুমাত্র এডমিন এক্সেস পাবে

st.title("⚙️ System Admin")

tab1, tab2, tab3 = st.tabs(["📜 Activity Logs", "📦 Inventory", "📥 Export Data"])

# --- LOGS ---
with tab1:
    if st.button("Clear Logs"):
        st.session_state.logs = []
        st.rerun()
    
    if 'logs' in st.session_state:
        for log in st.session_state.logs:
            st.text(log)
    else:
        st.info("No recent activities.")

# --- INVENTORY ---
with tab2:
    st.subheader("Manage T-Shirt Stock")
    cols = st.columns(5)
    for i, s in enumerate(["S", "M", "L", "XL", "XXL"]):
        cols[i].metric(s, st.session_state.stock.get(s, 0))
    
    with st.form("update_stock"):
        sz = st.selectbox("Select Size", ["S", "M", "L", "XL", "XXL"])
        qty = st.number_input("New Quantity", min_value=0)
        
        if st.form_submit_button("Update Stock"):
            st.session_state.stock[sz] = qty
            # গুগল শিটে আপডেট
            data = [{"Size": k, "Quantity": v} for k, v in st.session_state.stock.items()]
            utils.get_conn().update(worksheet="Stock", data=pd.DataFrame(data))
            st.success(f"Stock for {sz} updated to {qty}")
            st.rerun()

# --- EXPORT ---
with tab3:
    st.subheader("Download Bus Manifest")
    if st.button("📄 Generate Signature Sheet"):
        html = """
        <html>
        <head>
            <style>
                body { font-family: sans-serif; }
                table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
                th, td { border: 1px solid black; padding: 8px; text-align: left; }
                h2 { border-bottom: 2px solid black; }
                .page-break { page-break-before: always; }
            </style>
        </head>
        <body>
        <h1>Bus Manifest - Final List</h1>
        """
        
        buses = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
        df = st.session_state.df
        
        for b in buses:
            b_df = df[df['Bus_Number'] == b]
            if not b_df.empty:
                html += f"<h2>{b} (Total: {len(b_df)})</h2>"
                html += "<table><tr><th>Sl.</th><th>Name</th><th>Class</th><th>Ticket</th><th>In Sign</th><th>Out Sign</th></tr>"
                for i, (_, row) in enumerate(b_df.iterrows(), 1):
                    html += f"<tr><td>{i}</td><td>{row['Name']}</td><td>{row['Class']}</td><td>{row['Ticket_Number']}</td><td></td><td></td></tr>"
                html += "</table><div class='page-break'></div>"
        
        html += "</body></html>"
        
        st.download_button(
            label="⬇️ Download HTML File",
            data=html,
            file_name="Bus_Manifest_Printable.html",
            mime="text/html"
        )
