# 💳 信用卡優惠戰情室

銀行信用卡優惠爬蟲與管理系統

## 功能

- 🔄 自動爬取三家銀行優惠（中國信託、國泰世華、聯邦銀行）
- 🔍 關鍵字搜尋與篩選
- 💳 個人信用卡管理（CRUD）
- 🎨 三種主題（深色/亮色/海洋）
- 🗺️ 地圖搜尋功能

## 快速開始

### 本地運行

```bash
# 安裝依賴
pip install streamlit pandas

# 啟動應用
streamlit run app_streamlit.py
```

### 執行爬蟲

```bash
# 安裝爬蟲依賴
pip install playwright
playwright install chromium

# 執行爬蟲
python run_scraper.py
```

## 部署

### Streamlit Cloud

1. Fork 此專案到你的 GitHub
2. 到 [share.streamlit.io](https://share.streamlit.io) 登入
3. 選擇你的 repo 和 `app_streamlit.py`
4. 點擊 Deploy

### GitHub Actions 自動爬蟲

專案已設定每日自動執行爬蟲（台灣時間 08:00），結果會自動 commit 回 repo。

## 檔案結構

```
ccard/
├── app_streamlit.py        # Streamlit UI
├── run_scraper.py          # 爬蟲主程式
├── database.py             # 資料庫操作
├── scrapers/               # 爬蟲模組
│   ├── ctbc.py            # 中國信託
│   ├── cathay.py          # 國泰世華
│   └── ubot.py            # 聯邦銀行
├── .github/workflows/      # GitHub Actions
└── .streamlit/config.toml  # Streamlit 設定
```

## License

MIT
