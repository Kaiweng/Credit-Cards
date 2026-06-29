# src/utils/test_core.py
from src.core.db_manager import init_db, get_db_cursor
import os

def test_db_init():
    print("正在測試資料庫初始化...")
    init_db()
    assert os.path.exists("credit_cards.db"), "資料庫檔案未建立"
    print("✅ 資料庫初始化測試通過")

def test_crud_operations():
    print("正在測試 CRUD 運作...")
    with get_db_cursor() as cursor:
        # 測試插入
        cursor.execute("INSERT INTO cards (bank, card_name) VALUES (?, ?)", ("測試銀行", "測試信用卡"))
        # 測試查詢
        cursor.execute("SELECT * FROM cards WHERE card_name = ?", ("測試信用卡",))
        card = cursor.fetchone()
        assert card is not None, "資料寫入失敗"
        print(f"✅ 成功讀取卡片: {card['card_name']}")
        # 測試清理
        cursor.execute("DELETE FROM cards WHERE card_name = ?", ("測試信用卡",))

if __name__ == "__main__":
    test_db_init()
    test_crud_operations()
    print("🎉 所有核心測試通過！")
