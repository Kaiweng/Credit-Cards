import pandas as pd
import sqlite3
import os
from database import init_db, add_offers, clear_offers, DB_NAME

def rebuild_db():
    print("Beginning DB Rebuild...")
    
    # 1. Drop existing table to force schema update
    # Since sqlite doesn't support easy column addition if we want cleanness,
    # and we have the source data in CSV, dropping tables is safest (except cards if user has them).
    # But wait, user might have cards in 'cards' table. 'init_db' handles both.
    # I should only drop 'offers' table if possible, or migrate.
    
    # Since we modified init_db to create 'offers' with image, 
    # we can drop 'offers' table manually first.
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DROP TABLE IF EXISTS offers")
        print("Dropped 'offers' table.")
    except Exception as e:
        print(f"Error dropping table: {e}")
    conn.commit()
    conn.close()
    
    # 2. Re-initialize DB (will create new 'offers' table with 'image' col)
    init_db()
    
    # 3. Load data from CSV
    if os.path.exists("all_bank_offers.csv"):
        try:
            df = pd.read_csv("all_bank_offers.csv")
            # Fill NaN with None/Empty
            df = df.fillna("")
            
            offers = df.to_dict('records')
            
            # 4. Insert into DB
            add_offers(offers)
            print(f"Successfully imported {len(offers)} offers from CSV.")
        except Exception as e:
            print(f"Error reading/importing CSV: {e}")
    else:
        print("all_bank_offers.csv not found!")

if __name__ == "__main__":
    rebuild_db()
