# src/backend/core/database.py
import sqlite3
import os
import urllib.request
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "credit_cards.db")

def bootstrap_db():
    download_url = os.environ.get("DB_DOWNLOAD_URL")
    if download_url:
        try:
            print(f"正在從 {download_url} 下載最新資料庫...")
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            req = urllib.request.Request(
                download_url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req) as response, open(DB_PATH, 'wb') as out_file:
                out_file.write(response.read())
            print("資料庫下載並更新完成！")
        except Exception as e:
            print(f"下載資料庫失敗: {e}，將使用現有的資料庫檔案。")

# 自動執行資料庫自適應載入
bootstrap_db()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    return conn

def fetch_offers(search=None, bank=None, category=None):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM offers WHERE 1=1"
    params = []
    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")
    if bank:
        query += " AND bank = ?"
        params.append(bank)
    if category:
        query += " AND category = ?"
        params.append(category)
    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return [r for r in results if r['title'] and len(str(r['title'])) > 2]

def get_filters():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT bank FROM offers WHERE bank IS NOT NULL")
    banks = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT category FROM offers WHERE category IS NOT NULL")
    categories = [row[0] for row in cursor.fetchall()]
    
    # 查詢資料庫中最新的更新時間
    cursor.execute("SELECT MAX(scraped_at) FROM offers")
    last_update_val = cursor.fetchone()[0]
    conn.close()
    
    last_update = "無資料"
    if last_update_val:
        # 將 ISO 格式轉為顯示格式
        try:
            # 處理可能帶有微秒數的 ISO 字串
            dt = datetime.fromisoformat(last_update_val.split('.')[0])
            last_update = dt.strftime("%Y-%m-%d %H:%M")
        except:
            last_update = last_update_val
        
    return {"banks": banks, "categories": categories, "last_update": last_update}
