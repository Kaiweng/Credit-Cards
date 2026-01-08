# -*- coding: utf-8 -*-
"""
信用卡優惠戰情室
Streamlit UI 應用程式 - 美化版
"""

import streamlit as st
import subprocess
import sys
import os
from datetime import datetime
from database import (
    init_db, get_offers, get_offer_stats, get_banks, get_categories,
    get_cards, add_card, update_card, delete_card, get_card
)
from geopy.geocoders import Nominatim
import pandas as pd
import requests
import base64


# ============================================================
# 頁面設定
# ============================================================
st.set_page_config(
    page_title="💳 信用卡優惠戰情室",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 主題設定
# ============================================================
THEMES = {
    "🌙 深色主題": {
        "bg_primary": "#1a1a2e",
        "bg_secondary": "#16213e",
        "bg_card": "#0f3460",
        "text_primary": "#ffffff",
        "text_secondary": "#a0a0a0",
        "accent": "#e94560",
        "css": """
            .stApp { background-color: #1a1a2e; }
            
            /* 所有文字顏色 */
            .stApp, .stApp p, .stApp span, .stApp div, .stApp label { color: #ffffff !important; }
            .stMarkdown, .stMarkdown p { color: #ffffff !important; }
            .stCaption, [data-testid="stCaptionContainer"] { color: #a0a0a0 !important; }
            
            /* 表單元素 */
            .stSelectbox label, .stTextInput label, .stNumberInput label, .stTextArea label { color: #ffffff !important; }
            .stSelectbox [data-baseweb="select"] span { color: #ffffff !important; }
            .stTextInput input, .stNumberInput input, .stTextArea textarea { color: #ffffff !important; background-color: #16213e !important; }
            
            /* 指標 */
            .stMetric label { color: #a0a0a0 !important; }
            .stMetric [data-testid="stMetricValue"] { color: #ffffff !important; }
            
            /* 標題 */
            h1, h2, h3, h4, h5, h6 { color: #ffffff !important; }
            .stHeader, [data-testid="stHeader"] { color: #ffffff !important; }
            
            /* 側邊欄 */
            [data-testid="stSidebar"], [data-testid="stSidebar"] * { color: #ffffff !important; }
            [data-testid="stSidebar"] { background-color: #16213e !important; }
            
            /* Radio 按鈕 */
            .stRadio label { color: #ffffff !important; }
            
            /* Info/Warning 框 */
            .stAlert { color: #ffffff !important; }
        """
    },
    "☀️ 亮色主題": {
        "bg_primary": "#f8f9fa",
        "bg_secondary": "#ffffff",
        "bg_card": "#e9ecef",
        "text_primary": "#212529",
        "text_secondary": "#6c757d",
        "accent": "#dc3545",
        "css": """
            .stApp { background-color: #f8f9fa; }
        """
    },
    "🌊 海洋主題": {
        "bg_primary": "#0a192f",
        "bg_secondary": "#112240",
        "bg_card": "#1d3557",
        "text_primary": "#ccd6f6",
        "text_secondary": "#8892b0",
        "accent": "#64ffda",
        "css": """
            .stApp { background-color: #0a192f; }
            
            /* 所有文字顏色 */
            .stApp, .stApp p, .stApp span, .stApp div, .stApp label { color: #ccd6f6 !important; }
            .stMarkdown, .stMarkdown p { color: #ccd6f6 !important; }
            .stCaption, [data-testid="stCaptionContainer"] { color: #8892b0 !important; }
            
            /* 表單元素 */
            .stSelectbox label, .stTextInput label, .stNumberInput label, .stTextArea label { color: #ccd6f6 !important; }
            .stSelectbox [data-baseweb="select"] span { color: #ccd6f6 !important; }
            .stTextInput input, .stNumberInput input, .stTextArea textarea { color: #ccd6f6 !important; background-color: #112240 !important; }
            
            /* 指標 */
            .stMetric label { color: #8892b0 !important; }
            .stMetric [data-testid="stMetricValue"] { color: #64ffda !important; }
            
            /* 標題 */
            h1, h2, h3, h4, h5, h6 { color: #ccd6f6 !important; }
            
            /* 側邊欄 */
            [data-testid="stSidebar"], [data-testid="stSidebar"] * { color: #ccd6f6 !important; }
            [data-testid="stSidebar"] { background-color: #112240 !important; }
            
            /* Radio 按鈕 */
            .stRadio label { color: #ccd6f6 !important; }
        """
    }
}

# 銀行顏色
BANK_COLORS = {
    "中國信託": "#00A651",
    "國泰世華": "#E60012", 
    "聯邦銀行": "#0066CC",
}

def get_bank_color(bank_name: str) -> str:
    for key, color in BANK_COLORS.items():
        if key in bank_name:
            return color
    return "#6c757d"

# ============================================================
# 初始化
# ============================================================
init_db()

# Function to fetch image bytes (Bypasses Hotlink Protection)
# Using st.cache_data as verified in image_verifier.py
@st.cache_data(show_spinner=False)
def fetch_image_bytes(url):
    if not url or not isinstance(url, str):
        return None
    try:
        # User-Agent to mimic a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "" # Empty referer sometimes helps, or mimic the bank site
        }
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            return r.content
    except:
        pass
    return None

# Session state
if "theme" not in st.session_state:
    st.session_state.theme = "🌙 深色主題"

# ============================================================
# 側邊欄
# ============================================================
with st.sidebar:
    st.title("💳 信用卡優惠戰情室")
    
    # 簡潔統計 (放在標題下方)
    stats = get_offer_stats()
    by_bank = stats.get("by_bank", {})
    st.caption(f"📊 總計 {stats.get('total', 0)} 筆 | 🟢 中信 {by_bank.get('中國信託', 0)} | 🔴 國泰 {by_bank.get('國泰世華', 0)} | 🔵 聯邦 {by_bank.get('聯邦銀行', 0)}")
    
    st.divider()
    
    # 主題選擇
    st.session_state.theme = st.selectbox(
        "🎨 選擇主題",
        list(THEMES.keys()),
        index=list(THEMES.keys()).index(st.session_state.theme)
    )
    
    st.divider()
    
    # 頁面選擇
    # 頁面選擇
    page = st.radio("功能選擇", ["💰 優惠瀏覽", "💳 信用卡管理"], label_visibility="collapsed")
    
    st.divider()
    
    # 我的信用卡快速檢視
    my_cards = get_cards()
    if my_cards:
        st.subheader("📌 我的信用卡")
        for card in my_cards:
            bank_color = get_bank_color(card.get("bank", ""))
            st.markdown(f"""
                <div style="background:{bank_color}; color:white; padding:8px 12px; 
                     border-radius:8px; margin:5px 0; font-size:0.85rem;">
                    <strong>{card.get('bank', '')}</strong><br>
                    {card.get('card_name', '')}
                </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # 顯示資料庫更新時間
    offers_file = os.path.join(os.path.dirname(__file__), "all_bank_offers.json")
    if os.path.exists(offers_file):
        mtime = os.path.getmtime(offers_file)
        update_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        st.caption(f"📅 資料更新時間: {update_time}")
    else:
        st.caption("📅 尚無資料")
    
    if st.button("🔄 更新資料（執行爬蟲）", use_container_width=True):
        with st.spinner("正在爬取資料..."):
            try:
                # 使用相對路徑執行 scraper
                scraper_script = os.path.join(os.path.dirname(__file__), "bank_offers_scraper.py")
                subprocess.run([sys.executable, scraper_script], 
                             cwd=os.path.dirname(__file__),
                             check=True)
                st.success("更新完成！")
                st.rerun()
            except Exception as ex:
                st.error(f"更新失敗: {ex}")


# ============================================================
# 套用主題 CSS
# ============================================================
theme = THEMES[st.session_state.theme]
st.markdown(f"""
<style>
    {theme['css']}
    
    /* 銀行標籤 */
    .bank-tag {{
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.85rem;
        color: white;
        display: inline-block;
    }}
    
    /* 優惠卡片 */
    .offer-row {{
        background: {theme['bg_secondary']};
        border-radius: 10px;
        padding: 12px 15px;
        margin: 8px 0;
        border-left: 4px solid {theme['accent']};
    }}
    
    /* 信用卡卡片 */
    .card-item {{
        background: {theme['bg_secondary']};
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid {theme['bg_card']};
    }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 優惠瀏覽頁面
# ============================================================
if page == "💰 優惠瀏覽":
    
    # 搜尋與篩選
    col1, col2, col3, col4 = st.columns([3, 1.5, 1.5, 2])
    with col1:
        search_term = st.text_input("🔍 搜尋優惠", placeholder="輸入關鍵字...")
    with col2:
        banks = ["全部"] + get_banks()
        selected_bank = st.selectbox("銀行", banks)
    with col3:
        categories = ["全部"] + get_categories()
        selected_category = st.selectbox("分類", categories)
    with col4:
        # 我的卡片篩選
        my_cards = get_cards()
        card_options = ["不限"] + [f"{c['bank']} - {c['card_name']}" for c in my_cards]
        selected_my_card = st.selectbox("🎯 我的信用卡", card_options)
    
    # 根據選擇的信用卡自動設定銀行篩選
    bank_filter = ""
    if selected_my_card != "不限":
        # 從選擇的卡片提取銀行名
        bank_filter = selected_my_card.split(" - ")[0]
    elif selected_bank != "全部":
        bank_filter = selected_bank
    
    cat_filter = selected_category if selected_category != "全部" else ""
    offers = get_offers(search=search_term, bank=bank_filter, category=cat_filter)
    
    st.caption(f"共 {len(offers)} 筆優惠")
    
    # ============================================================
    # V4 佈局：左右分割 (左列表 | 右地圖)
    # ============================================================
    # 使用 st.columns 建立左右區塊 (比例 3:2)
    left_panel, right_panel = st.columns([3, 2])
    
    # --- 左側：優惠列表 (可捲動) ---
    with left_panel:
        with st.container(border=True, height=600):
            st.subheader("📋 優惠列表")
            
            # 使用較小的字體 CSS
            st.markdown("""
            <style>
                .small-font { font-size: 0.9rem !important; }
                .offer-title { font-size: 1.05rem !important; font-weight: bold; }
            </style>
            """, unsafe_allow_html=True)
            
            
            # 多欄卡片式排版
            num_cols = 3  # 每列顯示3張卡片
            
            # 將 offers 分成多列
            for row_start in range(0, len(offers), num_cols):
                row_offers = offers[row_start:row_start + num_cols]
                cols = st.columns(num_cols)
                
                for idx, offer in enumerate(row_offers):
                    bank = offer.get("bank", "")
                    category = offer.get("category", "")
                    title = offer.get("title", "")
                    url = offer.get("url", "")
                    image = offer.get("image", "")
                    bank_color = get_bank_color(bank)
                    
                    with cols[idx]:
                        with st.container(border=True):
                            # 圖片區 (無 caption，避免重複標題)
                            valid_image = image
                            if image and "icon_clock" in image:
                                valid_image = None
                            
                            if valid_image:
                                try:
                                    img_bytes = fetch_image_bytes(valid_image)
                                    if img_bytes:
                                        st.image(img_bytes, use_column_width=True)
                                    else:
                                        st.image(valid_image, use_column_width=True)
                                except Exception:
                                    st.markdown('<div style="height:80px; background:#f0f2f6; border-radius:5px; display:flex; align-items:center; justify-content:center;">🖼️</div>', unsafe_allow_html=True)
                            else:
                                st.markdown('<div style="height:80px; background:#f0f2f6; border-radius:5px; display:flex; align-items:center; justify-content:center;">🖼️</div>', unsafe_allow_html=True)
                            
                            # 標題 (連結)
                            if url:
                                st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none; color:inherit; font-weight:bold; font-size:0.9rem; display:block; margin-top:8px;">{title}</a>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<span style="font-weight:bold; font-size:0.9rem; display:block; margin-top:8px;">{title}</span>', unsafe_allow_html=True)
                            
                            # 銀行 + 分類標籤
                            st.markdown(f'''
                                <div style="margin-top:6px;">
                                    <span style="background:{bank_color}; color:white; padding:3px 8px; border-radius:4px; font-size:0.7rem;">{bank}</span>
                                    <span style="color:gray; font-size:0.75rem; margin-left:6px;">{category}</span>
                                </div>
                            ''', unsafe_allow_html=True)

    # --- 右側：地圖整合 (固定高度視窗) ---
    with right_panel:
        with st.container(border=True, height=600):
            st.subheader("🗺️ 地點搜尋")
            
            # 只有當有搜尋關鍵字時，才嘗試顯示相關地圖
            if search_term:
                st.info(f"📍 搜尋：'{search_term}'")
                
                try:
                    # 建立 geolocator
                    geolocator = Nominatim(user_agent="credit_card_app_taiwan_refine_v4")
                    location = geolocator.geocode(search_term)
                    
                    if location:
                        map_data = pd.DataFrame([{
                            'lat': location.latitude,
                            'lon': location.longitude,
                            'name': search_term
                        }])
                        st.map(map_data, zoom=15, use_container_width=True)
                        
                        # Google Maps 按鈕
                        google_maps_url = f"https://www.google.com/maps/search/?api=1&query={search_term}"
                        st.link_button("🌏 在 Google 地圖開啟 (查看評論/導航)", google_maps_url, use_container_width=True)
                        
                    else:
                        st.warning(f"⚠️ 無法在地圖上找到 '{search_term}'")
                        default_map = pd.DataFrame([{'lat': 25.0478, 'lon': 121.5171, 'name': '台北車站'}])
                        st.map(default_map, zoom=12, use_container_width=True)
                        
                except Exception as e:
                    st.error("地圖服務暫時忙碌中")
            else:
                st.caption("👈 請在左上方輸入關鍵字搜尋")
                default_map = pd.DataFrame([{'lat': 25.0478, 'lon': 121.5171, 'name': '台北車站'}])
                st.map(default_map, zoom=12, use_container_width=True)


# ============================================================
# 信用卡管理頁面
# ============================================================
elif page == "💳 信用卡管理":
    st.header("我的信用卡")
    
    # 新增信用卡表單
    with st.expander("➕ 新增信用卡", expanded=False):
        with st.form("add_card_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                new_bank = st.selectbox("銀行 *", ["中國信託", "國泰世華", "聯邦銀行", "其他"])
                if new_bank == "其他":
                    new_bank = st.text_input("請輸入銀行名稱")
                new_name = st.text_input("卡片名稱 *")
            with col2:
                new_type = st.text_input("卡別 (如: 御璽卡/白金卡)")
                new_fee = st.text_input("年費")
            with col3:
                new_billing = st.number_input("結帳日 (1-31)", min_value=1, max_value=31, value=15)
                new_payment = st.number_input("繳款日 (1-31)", min_value=1, max_value=31, value=25)
            
            new_notes = st.text_area("備註")
            
            if st.form_submit_button("新增", use_container_width=True, type="primary"):
                if new_bank and new_name:
                    add_card(new_bank, new_name, new_type, new_fee, new_billing, new_payment, new_notes)
                    st.success("新增成功！")
                    st.rerun()
                else:
                    st.error("請填寫銀行與卡片名稱")
    
    st.divider()
    
    # 信用卡列表
    cards = get_cards()
    
    if not cards:
        st.info("尚無信用卡資料，請先新增")
    else:
        for card in cards:
            card_id = card.get("id")
            bank = card.get("bank", "")
            card_name = card.get("card_name", "")
            card_type = card.get("card_type", "")
            annual_fee = card.get("annual_fee", "")
            billing_day = card.get("billing_day", "")
            payment_day = card.get("payment_day", "")
            notes = card.get("notes", "")
            bank_color = get_bank_color(bank)
            
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([1.5, 3, 2, 0.5, 0.5])
                with col1:
                    st.markdown(f'<span class="bank-tag" style="background:{bank_color}">{bank}</span>', 
                               unsafe_allow_html=True)
                with col2:
                    st.markdown(f"**{card_name}**")
                    st.caption(f"{card_type} | 年費: {annual_fee or '無'}")
                with col3:
                    if billing_day and payment_day:
                        st.caption(f"📅 結帳日: {billing_day}日 | 繳款日: {payment_day}日")
                with col4:
                    if st.button("✏️", key=f"edit_{card_id}", help="編輯"):
                        st.session_state[f"editing_{card_id}"] = True
                with col5:
                    if st.button("🗑️", key=f"del_{card_id}", help="刪除"):
                        delete_card(card_id)
                        st.rerun()
                
                # 編輯表單
                if st.session_state.get(f"editing_{card_id}"):
                    with st.form(f"edit_form_{card_id}"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            edit_bank = st.text_input("銀行", value=bank)
                            edit_name = st.text_input("卡片名稱", value=card_name)
                        with col2:
                            edit_type = st.text_input("卡別", value=card_type)
                            edit_fee = st.text_input("年費", value=annual_fee)
                        with col3:
                            edit_billing = st.number_input("結帳日", min_value=1, max_value=31, 
                                                          value=billing_day if billing_day else 15)
                            edit_payment = st.number_input("繳款日", min_value=1, max_value=31,
                                                          value=payment_day if payment_day else 25)
                        edit_notes = st.text_area("備註", value=notes)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("儲存", type="primary"):
                                update_card(card_id, edit_bank, edit_name, edit_type, edit_fee,
                                           edit_billing, edit_payment, edit_notes)
                                st.session_state[f"editing_{card_id}"] = False
                                st.rerun()
                        with col2:
                            if st.form_submit_button("取消"):
                                st.session_state[f"editing_{card_id}"] = False
                                st.rerun()
                
                st.divider()

# ============================================================
# 地圖搜尋頁面
# ============================================================

