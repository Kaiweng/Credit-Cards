# -*- coding: utf-8 -*-
"""
資料庫操作模組
包含優惠與信用卡的 CRUD 功能
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

DB_NAME = "credit_cards.db"


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
    # Note: Adding image column. If table exists, this won't run unless dropped.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank TEXT NOT NULL,
            category TEXT,
            title TEXT NOT NULL,
            url TEXT,
            image TEXT,
            scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
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
    
    for o in offers:
        cursor.execute("""
            INSERT INTO offers (bank, category, title, url, image, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (o.get("bank"), o.get("category"), o.get("title"), o.get("url"), o.get("image"), now))
    
    conn.commit()
    conn.close()
    print(f"已新增 {len(offers)} 筆優惠")


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
