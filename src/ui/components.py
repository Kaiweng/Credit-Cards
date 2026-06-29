# src/ui/components.py
import streamlit as st

def render_offer_card(offer, bank_color):
    """渲染單一優惠卡片"""
    with st.container(border=True):
        st.markdown(f"**{offer['title']}**")
        st.markdown(f'<span style="background:{bank_color}; color:white; padding:2px 6px; border-radius:4px; font-size:0.7rem;">{offer["bank"]}</span>', unsafe_allow_html=True)
        if offer['url']:
            st.link_button("前往連結", offer['url'], use_container_width=True)
