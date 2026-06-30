# -*- coding: utf-8 -*-
"""
資料庫操作模組
包含優惠與信用卡的 CRUD 功能
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

# 使用相對路徑確保在不同執行目錄下都能讀取到資料庫
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "credit_cards.db")


def get_connection():
    """取得資料庫連線"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化資料庫"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 優惠表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank TEXT NOT NULL,
            category TEXT,
            title TEXT NOT NULL,
            url TEXT,
            image TEXT,
            scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 檢查 offers 表是否已有 created_at 欄位，若無則新增 (適用於已存在的舊資料庫)
    cursor.execute("PRAGMA table_info(offers)")
    columns = [row[1] for row in cursor.fetchall()]
    if "created_at" not in columns:
        try:
            # 由於 SQLite 限制，我們分步執行 ALTER 與 UPDATE
            cursor.execute("ALTER TABLE offers ADD COLUMN created_at DATETIME")
            cursor.execute("UPDATE offers SET created_at = scraped_at WHERE created_at IS NULL")
            conn.commit()
            print("資料庫已成功新增 created_at 欄位")
        except Exception as e:
            print(f"新增 created_at 欄位失敗: {e}")
    
    # 信用卡表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank TEXT NOT NULL,
            card_name TEXT NOT NULL,
            card_type TEXT,
            annual_fee TEXT,
            billing_day INTEGER,
            payment_day INTEGER,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 建立索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_offers_bank ON offers(bank)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_offers_category ON offers(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_bank ON cards(bank)")
    
    conn.commit()
    conn.close()
    print("資料庫初始化完成")


# ============================================================
# 優惠 CRUD
# ============================================================

def clear_offers():
    """清除所有優惠資料"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM offers")
    conn.commit()
    conn.close()


def add_offers(offers: List[Dict]):
    """批量新增優惠"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    cursor.execute("PRAGMA table_info(offers)")
    columns = [row[1] for row in cursor.fetchall()]
    has_created_at = "created_at" in columns
    
    for o in offers:
        if has_created_at:
            cursor.execute("""
                INSERT INTO offers (bank, category, title, url, image, scraped_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (o.get("bank"), o.get("category"), o.get("title"), o.get("url"), o.get("image"), now, now))
        else:
            cursor.execute("""
                INSERT INTO offers (bank, category, title, url, image, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (o.get("bank"), o.get("category"), o.get("title"), o.get("url"), o.get("image"), now))
    
    conn.commit()
    conn.close()
    print(f"已新增 {len(offers)} 筆優惠")


def upsert_bank_offers(bank: str, offers: List[Dict]):
    """
    增量更新特定銀行的優惠。
    如果 offers 為 None，代表爬取失敗，不對資料庫做任何該銀行的變更以防止誤刪。
    """
    if offers is None:
        print(f"\n[{bank}] 傳入之優惠資料為 None (可能爬取失敗)，跳過資料庫更新以防止誤刪。")
        return
        
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    try:
        # 1. 取得資料庫中該銀行現有的所有優惠
        cursor.execute("SELECT id, title, url FROM offers WHERE bank = ?", (bank,))
        db_rows = cursor.fetchall()
        
        # 建立 (title, url) -> id 的對照表
        db_offers = {}
        for row in db_rows:
            db_offers[(row["title"], row["url"])] = row["id"]
            
        keep_ids = set()
        
        # 2. 遍歷本次爬到的優惠進行新增或更新
        insert_count = 0
        update_count = 0
        
        for o in offers:
            title = o.get("title")
            url = o.get("url")
            category = o.get("category")
            image = o.get("image")
            
            key = (title, url)
            if key in db_offers:
                db_id = db_offers[key]
                cursor.execute("""
                    UPDATE offers 
                    SET category = ?, image = ?, scraped_at = ?
                    WHERE id = ?
                """, (category, image, now, db_id))
                keep_ids.add(db_id)
                update_count += 1
            else:
                cursor.execute("""
                    INSERT INTO offers (bank, category, title, url, image, scraped_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (bank, category, title, url, image, now, now))
                insert_count += 1
                
        # 3. 刪除該銀行在資料庫中已失效（即本次沒爬到）的舊優惠
        all_db_ids = set(db_offers.values())
        delete_ids = all_db_ids - keep_ids
        
        if delete_ids:
            placeholders = ",".join("?" for _ in delete_ids)
            cursor.execute(f"""
                DELETE FROM offers 
                WHERE id IN ({placeholders})
            """, tuple(delete_ids))
            print(f"[{bank}] 已從資料庫刪除 {len(delete_ids)} 筆失效優惠")
            
        conn.commit()
        print(f"[{bank}] 增量更新完成。新增 {insert_count} 筆，更新 {update_count} 筆。")
    except Exception as e:
        conn.rollback()
        print(f"[{bank}] 增量更新失敗: {e}")
        raise e
    finally:
        conn.close()


def get_offers(search: str = "", bank: str = "", category: str = "") -> List[Dict]:
    """查詢優惠"""
    conn = get_connection()
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
    
    query += " ORDER BY id DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_offer_stats() -> Dict:
    """取得優惠統計"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 總數
    cursor.execute("SELECT COUNT(*) FROM offers")
    total = cursor.fetchone()[0]
    
    # 各銀行統計
    cursor.execute("SELECT bank, COUNT(*) as count FROM offers GROUP BY bank")
    by_bank = {row["bank"]: row["count"] for row in cursor.fetchall()}
    
    # 最後更新時間
    cursor.execute("SELECT MAX(scraped_at) FROM offers")
    last_update = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total": total,
        "by_bank": by_bank,
        "last_update": last_update
    }


def get_banks() -> List[str]:
    """取得所有銀行"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT bank FROM offers WHERE bank IS NOT NULL ORDER BY bank")
    banks = [row[0] for row in cursor.fetchall()]
    conn.close()
    return banks


def get_categories(bank: str = "") -> List[str]:
    """取得所有分類"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if bank:
        cursor.execute("SELECT DISTINCT category FROM offers WHERE bank = ? AND category IS NOT NULL ORDER BY category", (bank,))
    else:
        cursor.execute("SELECT DISTINCT category FROM offers WHERE category IS NOT NULL ORDER BY category")
    
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    return categories


# ============================================================
# 信用卡 CRUD
# ============================================================

def add_card(bank: str, card_name: str, card_type: str = "", annual_fee: str = "", 
             billing_day: int = None, payment_day: int = None, notes: str = "") -> int:
    """新增信用卡"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO cards (bank, card_name, card_type, annual_fee, billing_day, payment_day, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (bank, card_name, card_type, annual_fee, billing_day, payment_day, notes, now, now))
    
    card_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return card_id


def update_card(card_id: int, bank: str = None, card_name: str = None, 
                card_type: str = None, annual_fee: str = None, 
                billing_day: int = None, payment_day: int = None, notes: str = None):
    """更新信用卡"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 取得現有資料
    cursor.execute("SELECT * FROM cards WHERE id = ?", (card_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    
    # 更新欄位
    new_bank = bank if bank is not None else row["bank"]
    new_card_name = card_name if card_name is not None else row["card_name"]
    new_card_type = card_type if card_type is not None else row["card_type"]
    new_annual_fee = annual_fee if annual_fee is not None else row["annual_fee"]
    new_billing_day = billing_day if billing_day is not None else row["billing_day"]
    new_payment_day = payment_day if payment_day is not None else row["payment_day"]
    new_notes = notes if notes is not None else row["notes"]
    now = datetime.now().isoformat()
    
    cursor.execute("""
        UPDATE cards 
        SET bank = ?, card_name = ?, card_type = ?, annual_fee = ?, billing_day = ?, payment_day = ?, notes = ?, updated_at = ?
        WHERE id = ?
    """, (new_bank, new_card_name, new_card_type, new_annual_fee, new_billing_day, new_payment_day, new_notes, now, card_id))
    
    conn.commit()
    conn.close()
    return True


def delete_card(card_id: int) -> bool:
    """刪除信用卡"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def get_cards(bank: str = "") -> List[Dict]:
    """查詢信用卡"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if bank:
        cursor.execute("SELECT * FROM cards WHERE bank = ? ORDER BY bank, card_name", (bank,))
    else:
        cursor.execute("SELECT * FROM cards ORDER BY bank, card_name")
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_card(card_id: int) -> Optional[Dict]:
    """取得單張信用卡"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cards WHERE id = ?", (card_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# 初始化
if __name__ == "__main__":
    init_db()
