# 💳 信用卡優惠戰情室 - Gemini 開發規範

此文件定義了 Antigravity AI 在處理「信用卡優惠戰情室」專案時必須遵循的規範與架構說明。

## 🌐 語言規範 (Language Policy)
- **必須使用繁體中文**：所有與使用者、技術文件、以及程式碼內部的註解（若為說明性質）均需使用繁體中文。
- **避免簡體中文**：嚴禁使用簡體中文詞彙。

## 🏗️ 專案架構 (Project Architecture)
本專案是一個基於 Python 的信用卡優惠整合平台，包含以下組件：
1. **資料來源 (Scrapers)**:
   - 使用 `Playwright` 進行網頁爬取。
   - 模組化設計：`scrapers/` 目錄下包含各銀行的獨立爬蟲。
   - 統一介面：繼承自 `BaseScraper`。
2. **資料存儲 (Database)**:
   - 使用 `SQLite` 存儲優惠與使用者信用卡資料。
   - 由 `database.py` 負責 CRUD 操作。
3. **前端展示 (UI)**:
   - 使用 `Streamlit` 建立互動式網格與地圖。
   - 支援多種主題與搜尋功能。

## 🛠️ 開發準則 (Development Guidelines)
- **新增銀行規範**：
  1. 在 `scrapers/` 下新增 `[bank].py`。
  2. 在 `scrapers/__init__.py` 註冊。
  3. 更新 `bank_offers_scraper.py` 以便 UI 觸發。
  4. 更新 `app_streamlit.py` 的顏色、Referer 與下拉選單。
- **UI 色彩**：各銀行需有代表性顏色，顯示於標籤或卡片邊框。
- **防盜連處理**：抓取圖片時若遇到 403，需在 `fetch_image_bytes` 中動態添加對應銀行的 `Referer`。

## 📌 重要路徑
- **資料庫**: `credit_cards.db`
- **主要爬蟲**: `bank_offers_scraper.py`
- **主要 UI**: `app_streamlit.py`
