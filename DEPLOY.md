# 部署指南

## 1. GitHub Actions 每日爬蟲

### 設定步驟

1. **建立 GitHub Repository**
   - 到 github.com 建立新的 repository
   - 將專案 push 上去

2. **啟用 Actions**
   - 到 repo 的 Settings > Actions > General
   - 確認 "Allow all actions" 已啟用

3. **設定寫入權限**
   - Settings > Actions > General > Workflow permissions
   - 選擇 "Read and write permissions"

4. **手動測試**
   - 到 Actions 頁面
   - 點擊 "Daily Credit Card Offers Scraper"
   - 點擊 "Run workflow" 手動執行測試

### 執行時間

- 每天 UTC 00:00（台灣時間 08:00）自動執行
- 可在 `.github/workflows/daily_scraper.yml` 修改 cron 表達式

---

## 2. Streamlit Cloud 部署

### 設定步驟

1. **準備 Repository**
   - 確保專案已 push 到 GitHub

2. **登入 Streamlit Cloud**
   - 到 https://share.streamlit.io
   - 使用 GitHub 帳號登入

3. **部署應用**
   - 點擊 "New app"
   - 選擇你的 repository
   - Branch: `main`
   - Main file path: `app_streamlit.py`
   - 點擊 "Deploy"

4. **設定 Requirements**
   - Streamlit Cloud 會自動讀取 `requirements.txt`
   - 如果需要分開管理，可以在 Advanced settings 指定 `requirements_streamlit.txt`

### 注意事項

- Streamlit Cloud **不支援 Playwright 爬蟲**，需使用 GitHub Actions 定時更新資料
- 確保 `credit_cards.db` 已 commit 到 repo

---

## 3. Push 到 GitHub

```powershell
cd "j:\我的云端硬盘\antigravity\ccard"

# 初始化 git（如果尚未）
git init

# 加入所有檔案
git add .

# 提交
git commit -m "Initial commit: Credit card offers system"

# 加入遠端（替換成你的 repo URL）
git remote add origin https://github.com/YOUR_USERNAME/ccard.git

# 推送
git push -u origin main
```
