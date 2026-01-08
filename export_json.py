import sqlite3
import pandas as pd
import json
import os

def export_data():
    # 1. 鎖定資料庫路徑
    base_path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_path, 'credit_cards.db')
    json_path = os.path.join(base_path, 'offers.json') # 輸出檔名

    print(f"📂 讀取資料庫: {db_path}")

    conn = sqlite3.connect(db_path)
    
    try:
        # 2. 【關鍵修正】讀取 'offers' 表格 (原本是 quick_offers)
        print("🔍 正在讀取 'offers' 資料表...")
        df = pd.read_sql("SELECT * FROM offers", conn)
        
        # 3. 資料處理 (確保欄位齊全)
        # 如果爬蟲沒抓圖片，補上空欄位，避免網頁報錯
        if 'image' not in df.columns:
            df['image'] = ""
        
        # 確保有 bank_name 欄位 (有些舊爬蟲是用 bank)
        if 'bank_name' not in df.columns and 'bank' in df.columns:
            df['bank_name'] = df['bank']

        # 4. 轉成 JSON
        offers_json = df.to_json(orient='records', force_ascii=False)
        
        # 5. 存檔
        parsed = json.loads(offers_json)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
            
        print(f"✅ 成功！已匯出 {len(df)} 筆資料。")
        print(f"📄 檔案位置: {json_path}")
        print("👉 下一步：請打開 GitHub Desktop，將 offers.json 推送 (Push) 到雲端。")
        
    except Exception as e:
        print(f"❌ 匯出失敗: {e}")
        print("   (請確認資料庫沒有被其他程式開啟)")
    finally:
        conn.close()

if __name__ == "__main__":
    export_data()