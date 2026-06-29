# 💳 信用卡優惠戰情室 (Credit Card Offers War Room)

基於 **FastAPI 後端 API** 與 **Vanilla HTML5 + TailwindCSS 前端** 的輕量、高質感信用卡優惠與管理系統。

## 🔄 系統功能
* **自動爬蟲更新**：使用 Playwright 爬取中國信託、國泰世華、聯邦銀行、玉山銀行最新優惠。
* **暗黑磨砂玻璃 UI**：精美的 Glassmorphism 設計，霓虹卡片發光 Hover 特效，以及自適應品牌色標籤。
* **即時數據統計**：頂部卡片即時顯示優惠統計筆數，支援銀行與分類的過濾器及關鍵字搜尋。
* **防圖片防盜連**：後端自帶 Proxy 代理與 HTTP 307 重定向，解決銀行網站對國外 IP 與網域的圖片限制。
* **每日自動更新**：整合 GitHub Actions，每天台灣時間 08:00 自動執行爬蟲更新並同步至線上。

---

## 📁 專案結構
```text
Credit-Cards/
├── docs/
│   └── index.html          # 前端靜態頁面 (GitHub Pages 部署路徑)
├── src/
│   └── backend/
│       ├── core/
│       │   └── database.py # 資料庫讀取與 bootstrap 下載邏輯
│       └── main.py         # FastAPI 後端 API (包含 CORS 與 API Key 驗證)
├── scrapers/               # 爬蟲子模組
├── bank_offers_scraper.py  # 爬蟲主程式 (會寫入 database 並重置 status.json)
├── credit_cards.db         # SQLite 資料庫 (存放爬取的優惠資料)
├── requirements.txt        # Python 依賴包設定
└── .github/workflows/
    └── daily_scraper.yml   # GitHub Actions 每日自動爬蟲排程
```

---

## 💻 本地端運行指南

### 1. 安裝環境依賴
在 Python 環境中執行：
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. 啟動後端服務
```bash
python -m src.backend.main
```
服務將啟動於 `http://localhost:8001`。

### 3. 本地執行爬蟲更新資料庫
```bash
python bank_offers_scraper.py
```

### 4. 開啟前端頁面
直接使用瀏覽器雙擊打開 `docs/index.html`（在本地偵測下會自動連接 `localhost:8001`）。

---

## 🚀 雲端自動化部署指南

本專案採用 **GitHub Pages** (前端) + **Render.com** (後端) + **GitHub Actions** (定時爬蟲媒介) 的免費輕量部署方案。

### 1. 前端部署 (GitHub Pages)
1. 確保專案中包含 `docs/index.html`，並將程式碼推上 GitHub。
2. 進入您的 GitHub Repository > **Settings** > **Pages**。
3. 在 **Branch** 選擇 `main`，資料夾選擇 `/docs`，然後點擊 **Save**。
4. 取得您的前端網址（例如：`https://<您的GitHub帳號>.github.io/Credit-Cards/`）。

### 2. 後端部署 (Render.com)
1. 在 Render 上新增一個 **Web Service**，連結您的 GitHub 專案。
2. 填寫部署設定：
   * **Runtime**: `Python`
   * **Build Command**: `pip install -r Credit-Cards/requirements.txt`
   * **Start Command**: `uvicorn src.backend.main:app --host 0.0.0.0 --port $PORT`
3. 進入 **Environment** 新增以下三個環境變數：
   * `DB_DOWNLOAD_URL`：`https://raw.githubusercontent.com/<您的GitHub帳號>/Credit-Cards/main/credit_cards.db` （後端重啟時自動拉取最新資料庫）
   * `ALLOWED_ORIGINS`：`https://<您的GitHub帳號>.github.io` （允許您的 Pages 前端跨域請求）
   * `API_KEY`：`您自訂的一組安全性金鑰` （保護爬蟲 API，防止被惡意呼叫）

### 3. 串接與 API 金鑰設定
1. 修改 `docs/index.html` 中的 `API_BASE`，將其指向您在 Render 拿到的網址。
2. 推送代碼：`git add . && git commit -m "Update API base" && git push`。
3. （可選）如果您設定了 `API_KEY`，請在您的前端網頁打開瀏覽器開發者工具 (F12) 的 **Console (主控台)**，輸入以下指令以啟用手動同步功能：
   ```javascript
   localStorage.setItem('apiKey', '您自訂的API_KEY');
   ```

---

## ⚙️ 自動更新排程
GitHub Actions 會在**每天早上 08:00 (台灣時間)** 自動執行一次爬網，將更新後的 SQLite 資料庫自動提交 Push 回 GitHub，Render 偵測到新 Commit 後便會自動重啟並下載新資料庫，全程無人值守。
