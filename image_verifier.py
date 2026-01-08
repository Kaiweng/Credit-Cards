
import streamlit as st
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
import time

st.set_page_config(page_title="圖片檢測工具", layout="wide")

st.title("🖼️ 信用卡優惠圖片檢測工具")

# Load Data
def load_data():
    try:
        df = pd.read_csv("all_bank_offers.csv")
        return df
    except Exception as e:
        st.error(f"無法讀取 CSV 檔案: {e}")
        return pd.DataFrame()

df = load_data()
df = df.fillna("")

if df.empty:
    st.stop()

# Sidebar
st.sidebar.header("設定")

# Filter by Bank
banks = ["全部"] + sorted(df['bank'].unique().tolist())
selected_bank = st.sidebar.selectbox("選擇銀行", banks)

# Filter Data
filtered_df = df.copy()
if selected_bank != "全部":
    filtered_df = filtered_df[filtered_df['bank'] == selected_bank]

# URL Checker Function
def check_url(url):
    if not isinstance(url, str) or not url.startswith("http"):
        return False, "無效連結"
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        if response.status_code == 200:
            return True, "OK"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, "Error"

# Batch Check Interface
st.sidebar.divider()
st.sidebar.subheader("🔗 連結檢測")

if "check_results" not in st.session_state:
    st.session_state.check_results = {}

if st.sidebar.button("開始檢測當前列表連結"):
    
    urls_to_check = filtered_df['image'].tolist()
    results = {}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total = len(urls_to_check)
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Create a list of futures
        future_to_url = {executor.submit(check_url, url): url for url in urls_to_check}
        
        completed = 0
        for future in future_to_url:
            url = future_to_url[future]
            try:
                is_valid, msg = future.result()
                results[url] = (is_valid, msg)
            except Exception as exc:
                results[url] = (False, "Exception")
            
            completed += 1
            progress_bar.progress(completed / total)
            status_text.text(f"檢測中... {completed}/{total}")
            
    st.session_state.check_results.update(results)
    st.sidebar.success("檢測完成！")

# Display Options
show_only_error = st.sidebar.checkbox("只顯示異常圖片", value=False)

# Main Content
st.write(f"顯示 {len(filtered_df)} 筆資料")

grid_cols = 3
cols = st.columns(grid_cols)

# Function to fetch image bytes (Bypasses Hotlink Protection)
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

for index, row in filtered_df.iterrows():
    
    img_url = row.get('image', '')
    title = row.get('title', 'No Title')
    bank_name = row.get('bank', '')
    
    # Check status from session state
    is_valid = True
    status_msg = "未檢測"
    if img_url in st.session_state.check_results:
        is_valid, status_msg = st.session_state.check_results[img_url]
    
    # Filter if "Show only error" is checked
    if show_only_error and is_valid and status_msg != "未檢測":
        continue
    if show_only_error and status_msg == "未檢測":
        pass 

    
    with cols[index % grid_cols]:
        with st.container(border=True):
            status_color = "green" if is_valid and status_msg == "OK" else "red" if not is_valid else "gray"
            st.markdown(f"**{bank_name}**")
            st.caption(f"[{status_msg}]", help=img_url)
            
            if img_url and isinstance(img_url, str) and img_url.strip():
                # Attempt to display image
                # First try direct URL (some might work), but since user reported issues,
                # let's try fetching bytes which is more robust against hotlinking.
                img_bytes = fetch_image_bytes(img_url)
                if img_bytes:
                     st.image(img_bytes, use_column_width=True, caption=title)
                else:
                    # Fallback to URL if bytes fetch fails (though unlikely if URL is good),
                    # or show error.
                     st.image(img_url, use_column_width=True, caption=title)
            else:
                st.info("無圖片連結")
            
            with st.expander("詳細資訊"):
                st.text(f"Title: {title}")
                st.text(f"URL: {img_url}")
