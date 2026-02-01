import streamlit as st
import utils

utils.init_page("Dashboard")
if not st.session_state.get('logged_in'): st.stop()

df = st.session_state.df
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total", len(df))
c2.metric("Checked-In", len(df[df['Entry_Status']=='Done']))
c3.metric("Kits", len(df[df['T_Shirt_Collected']=='Yes']))
# Food এরর ফিক্স - কলাম না থাকলেও ক্রাশ করবে না
food_cnt = len(df[df['Food_Collected']=='Yes']) if 'Food_Collected' in df.columns else 0
c4.metric("Meals", food_cnt)

st.dataframe(df[df['Entry_Status']=='Done'].head(10))
