# src/core/db_manager.py
import sqlite3
import os
from contextlib import contextmanager

# 資料庫路徑指向專案根目錄
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "credit_cards.db")

@contextmanager
def get_db_cursor():
    """使用 Context Manager 確保連線自動關閉"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """初始化資料庫架構"""
    with get_db_cursor() as cursor:
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
