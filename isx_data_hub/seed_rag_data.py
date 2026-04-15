import sqlite3
import os
from datetime import datetime, timedelta

db_path = r"E:\Kronos-master\isx_data_hub\isx_nucleus.db"

def seed_data():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all companies
    cursor.execute("SELECT id, symbol, name FROM companies")
    companies = cursor.fetchall()
    
    print(f"Seeding RAG data for {len(companies)} companies...")
    
    for company_id, symbol, name in companies:
        # 1. Seed News
        news_items = [
            (company_id, (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'), 
             f"{name} Announces Quarterly Profits", 
             f"The Board of Directors of {name} ({symbol}) announced a 15% increase in profits compared to the previous quarter, driven by operational expansion."),
            (company_id, (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'), 
             f"General Assembly Meeting for {symbol}", 
             f"{name} held its general assembly meeting to discuss the distribution of dividends to shareholders.")
        ]
        cursor.executemany("INSERT OR IGNORE INTO news (company_id, date, headline, content) VALUES (?, ?, ?, ?)", news_items)
        
        # 2. Seed Stakeholders
        stakeholders = [
            (company_id, "Iraqi Pension Fund", 12.5),
            (company_id, "Central Bank of Iraq", 5.0),
            (company_id, "Private Investment Group A", 8.3)
        ]
        cursor.executemany("INSERT OR IGNORE INTO stakeholders (company_id, owner_name, share_percentage) VALUES (?, ?, ?)", stakeholders)
        
        # 3. Seed Company Status
        cursor.execute("INSERT OR IGNORE INTO company_status (company_id, status, update_date, details) VALUES (?, ?, ?, ?)", 
                       (company_id, "Active", datetime.now().strftime('%Y-%m-%d'), "Trading normally on the main market floor."))
        
    conn.commit()
    conn.close()
    print("Seeding completed successfully.")

if __name__ == "__main__":
    seed_data()
