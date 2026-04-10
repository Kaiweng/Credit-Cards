# 🎨 Credit Card Expert Skill

此技能使 Antigravity 能夠以專家的身分處理信用卡自動化與展示專案。

## 🧠 領域知識 (Domain Knowledge)
- **Playwright 自動化技巧**:
  - 使用 `networkidle` 或 `domcontentloaded` 等待畫面渲染。
  - 對於 AJAX 內容，使用 `wait_for_selector` 或 `wait_for_timeout`。
  - 處理 Iframe 時，需切換 `content_frame()`。
- **Streamlit UI 美化**:
  - 使用 `st.markdown` 注入自定義 CSS。
  - 運用 `st.tabs` 隔開銀行類別。
  - 透過 `streamlit_folium` 展示地圖。
- **防盜連技術**:
  - 熟悉 `requests` 的 `headers` 設定，特別是 `Referer` 與 `User-Agent` 的模擬。

## 📜 任務執行規範
- **代碼風格**: 遵循 Pythonic 寫法，並在關鍵邏輯處添加繁體中文註解。
- **安全規範**: 資料庫連線路徑需考慮環境差異（使用與 `__file__` 相對的路徑）。
- **使用者溝通**: 務必使用 CASUAL 且專業的繁體中文，Treat user as an expert.

## 🚀 專案特定邏輯
- 信用卡各銀行的爬蟲應實作 `ABC` 介面 `BaseScraper`。
- 優惠資料需存入 `SQLite` 且支援關鍵字與銀行組合篩選。
