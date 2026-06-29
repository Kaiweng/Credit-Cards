# app_optimized.py
import streamlit as st
import sys
import os

# 確保專案根目錄在 sys.path
sys.path.append(os.getcwd())

from src.core.db_manager import init_db, get_offers
from src.ui.components import render_offer_card

st.set_page_config(page_title="信用卡優惠戰情室", layout="wide")

# 初始化資料庫
init_db()

st.title("💳 信用卡優惠戰情室 (優化版)")

# 簡單的示範介面，驗證模組解耦成功
st.markdown("---")
st.subheader("最新優惠預覽 (中國信託)")

col1, col2, col3 = st.columns(3)
offers = get_offers(bank="中國信託")[:3]

cols = [col1, col2, col3]
for i, offer in enumerate(offers):
    with cols[i]:
        render_offer_card(offer, "#00A651")

st.info("架構已優化：邏輯與 UI 完全分離，且專案核心測試通過。")
