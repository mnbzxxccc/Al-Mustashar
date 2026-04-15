import sqlite3
import os
import pandas as pd
import numpy as np

OLD_DB = "e:/Kronos-master/isx_data_hub/isx_nucleus.db"
NEW_DB = "e:/Kronos-master/isx_data_hub/isx_nucleus_enhanced.db"

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def migrate():
    if not os.path.exists(OLD_DB):
        print(f"❌ Error: {OLD_DB} not found.")
        return

    print(f"🔄 Migrating data from {OLD_DB} to {NEW_DB}...")
    
    old_conn = sqlite3.connect(OLD_DB)
    new_conn = sqlite3.connect(NEW_DB)
    
    # 1. Migrate Companies
    print("📈 Migrating Companies...")
    companies_df = pd.read_sql_query("SELECT symbol, name, sector FROM companies", old_conn)
    existing_companies = pd.read_sql_query("SELECT symbol FROM companies", new_conn)
    
    # Filter only new ones
    new_companies_df = companies_df[~companies_df['symbol'].isin(existing_companies['symbol'])]
    if not new_companies_df.empty:
        new_companies_df.to_sql("companies", new_conn, if_exists="append", index=False)
    
    # Map old IDs to new IDs (symbol is unique)
    new_companies = pd.read_sql_query("SELECT id, symbol FROM companies", new_conn)
    symbol_to_id = dict(zip(new_companies['symbol'], new_companies['id']))
    
    # 2. Migrate Prices
    print("💰 Migrating Prices (60k+ records)...")
    prices_df = pd.read_sql_query("SELECT * FROM prices", old_conn)
    
    # Get old symbols for mapping
    old_companies = pd.read_sql_query("SELECT id, symbol FROM companies", old_conn)
    old_id_to_symbol = dict(zip(old_companies['id'], old_companies['symbol']))
    
    # Replace old IDs with new ones
    prices_df['company_id'] = prices_df['company_id'].map(lambda x: symbol_to_id.get(old_id_to_symbol.get(x)))
    
    # Drop records that couldn't be mapped
    prices_df = prices_df.dropna(subset=['company_id'])
    
    # Remove 'id' column from prices to let the new DB auto-increment
    if 'id' in prices_df.columns:
        prices_df = prices_df.drop(columns=['id'])
        
    prices_df.to_sql("prices", new_conn, if_exists="append", index=False)

    # 3. Migrate News & Stakeholders if they exist
    print("📰 Migrating News & Stakeholders...")
    try:
        news_df = pd.read_sql_query("SELECT * FROM news", old_conn)
        news_df['company_id'] = news_df['company_id'].map(lambda x: symbol_to_id.get(old_id_to_symbol.get(x)))
        news_df.drop(columns=['id'], errors='ignore').to_sql("news", new_conn, if_exists="append", index=False)
    except: pass
    
    try:
        stk_df = pd.read_sql_query("SELECT * FROM stakeholders", old_conn)
        stk_df['company_id'] = stk_df['company_id'].map(lambda x: symbol_to_id.get(old_id_to_symbol.get(x)))
        stk_df.drop(columns=['id'], errors='ignore').to_sql("stakeholders", new_conn, if_exists="append", index=False)
    except: pass

    # 4. Generate Initial Technical Indicators for the Analysis Engine
    print("🤖 Generating Technical Indicators (RSI-14) for all stocks...")
    for symbol, cid in symbol_to_id.items():
        # Get last 50 days of close prices
        p_df = pd.read_sql_query(f"SELECT date, close FROM prices WHERE company_id = {cid} ORDER BY date ASC", new_conn)
        if len(p_df) > 15:
            rsi_vals = calculate_rsi(p_df['close'])
            latest_rsi = rsi_vals.iloc[-1]
            latest_date = p_df['date'].iloc[-1]
            
            if not np.isnan(latest_rsi):
                new_conn.execute("INSERT OR REPLACE INTO technical_indicators (company_id, date, rsi_14) VALUES (?, ?, ?)", 
                                 (cid, latest_date, float(latest_rsi)))

    new_conn.commit()
    old_conn.close()
    new_conn.close()
    print("✅ Migration Completed Successfully!")

if __name__ == "__main__":
    migrate()
