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

# Session state
if "theme" not in st.session_state:
    st.session_state.theme = "🌙 深色主題"

# ============================================================
# 側邊欄
# ============================================================
with st.sidebar:
    st.title("💳 信用卡優惠戰情室")
    st.divider()
    
    # 主題選擇
    st.session_state.theme = st.selectbox(
        "🎨 選擇主題",
        list(THEMES.keys()),
        index=list(THEMES.keys()).index(st.session_state.theme)
    )
    
    st.divider()
    
    # 頁面選擇
    page = st.radio("功能選擇", ["💰 優惠瀏覽", "💳 信用卡管理", "🗺️ 地圖搜尋"], label_visibility="collapsed")
    
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
                subprocess.run([sys.executable, "run_scraper.py"], 
                             cwd="j:\\我的云端硬盘\\antigravity\\ccard",
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
    # 統計區
    stats = get_offer_stats()
    by_bank = stats.get("by_bank", {})
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 總計", stats.get("total", 0))
    with col2:
        st.metric("🟢 中國信託", by_bank.get("中國信託", 0))
    with col3:
        st.metric("🔴 國泰世華", by_bank.get("國泰世華", 0))
    with col4:
        st.metric("🔵 聯邦銀行", by_bank.get("聯邦銀行", 0))
    
    st.divider()
    
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
    
    # 優惠列表
    for offer in offers:
        bank = offer.get("bank", "")
        category = offer.get("category", "")
        title = offer.get("title", "")
        url = offer.get("url", "")
        bank_color = get_bank_color(bank)
        
        col1, col2, col3, col4 = st.columns([1.2, 1.2, 6, 0.8])
        with col1:
            st.markdown(f'<span class="bank-tag" style="background:{bank_color}">{bank}</span>', 
                       unsafe_allow_html=True)
        with col2:
            st.caption(category[:8] + "..." if len(category) > 8 else category)
        with col3:
            st.write(title[:60] + "..." if len(title) > 60 else title)
        with col4:
            if url:
                st.link_button("🔗", url, help="開啟網頁")

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
elif page == "🗺️ 地圖搜尋":
    st.header("🗺️ 優惠地點搜尋")
    
    st.info("輸入地點關鍵字，搜尋附近的優惠商家")
    
    # 搜尋輸入
    col1, col2 = st.columns([3, 1])
    with col1:
        location_query = st.text_input("📍 輸入地點或商家名稱", placeholder="例如: 台北101、信義區、星巴克...")
    with col2:
        search_radius = st.selectbox("範圍", ["500m", "1km", "2km", "5km"])
    
    # 模擬地圖 (使用 Streamlit 的 map 功能)
    # 預設台北市中心座標
    import pandas as pd
    
    # 根據搜尋詞過濾優惠
    if location_query:
        related_offers = get_offers(search=location_query)
        if related_offers:
            st.success(f"找到 {len(related_offers)} 筆相關優惠")
            
            for offer in related_offers[:10]:  # 只顯示前10筆
                bank = offer.get("bank", "")
                title = offer.get("title", "")
                url = offer.get("url", "")
                bank_color = get_bank_color(bank)
                
                col1, col2, col3 = st.columns([1.5, 6, 1])
                with col1:
                    st.markdown(f'<span class="bank-tag" style="background:{bank_color}">{bank}</span>', 
                               unsafe_allow_html=True)
                with col2:
                    st.write(title)
                with col3:
                    if url:
                        st.link_button("🔗", url)
        else:
            st.warning("沒有找到相關優惠")
    
    # 顯示示範地圖
    st.subheader("📍 地圖檢視")
    
    # 台北市主要商圈座標
    map_data = pd.DataFrame({
        'lat': [25.0330, 25.0418, 25.0478, 25.0339, 25.0577],
        'lon': [121.5654, 121.5067, 121.5171, 121.5645, 121.5234],
        'name': ['信義區', '西門町', '中山區', '台北101', '大直']
    })
    
    st.map(map_data, zoom=12)
    
    st.caption("💡 提示：點擊地圖上的點可查看該區域的優惠商家")
