import time
import json
import os
import datetime
from isx_scraper import ISXScraper
from isx_manager import ISXManager

def fetch_cycle():
    scraper = ISXScraper()
    manager = ISXManager()
    
    print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Scheduled ISX Data Fetch...")
    
    # Load companies
    json_path = os.path.join(os.path.dirname(__file__), 'isx_companies.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            sectors = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {json_path}")
        return
        
    total_companies = sum(len(symbols) for symbols in sectors.values())
    print(f"Targeting {total_companies} companies to update...")
    
    processed = 0
    errors = []
    
    for sector, symbols in sectors.items():
        for symbol in symbols:
            processed += 1
            print(f"[{processed}/{total_companies}] Updating {symbol}...", end=" ", flush=True)
            
            try:
                # Ensure company metadata exists
                company_id = manager.save_company(symbol, name=symbol, sector=sector)
                
                # We fetch history for 2 years (or a very short period if it was a real API update, 
                # but since this is simulated, it will append/replace without duplicates due to UNIQUE constraints)
                df = scraper.fetch_history(symbol, years=2)
                
                if df is not None and not df.empty:
                    manager.save_prices(company_id, df)
                    print(f"OK ({len(df)} rows)")
                else:
                    print("No data")
                    errors.append(symbol)
                
                time.sleep(0.5) 
                
            except Exception as e:
                print(f"Error: {e}")
                errors.append(symbol)
    
    print("\nGeneration Complete.")
    print("Formatting and Exporting to Excel...")
    manager.export_to_excel()
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Cycle Complete. Waiting 20 hours for next cycle...\n")

if __name__ == "__main__":
    HOURS_TO_WAIT = 20
    WAIT_SECONDS = HOURS_TO_WAIT * 3600
    
    print("=========================================")
    print("ISX DATA HUB - 20HR AUTO FETCHER STARTED")
    print("=========================================")
    print(f"Will fetch prices and update the Nucleus database every {HOURS_TO_WAIT} hours.")
    print("Keep this window open to maintain automation.\n")
    
    while True:
        try:
            fetch_cycle()
        except Exception as e:
            print(f"\nCritical Error during fetch cycle: {e}")
            print("Retrying in the next cycle...")
            
        time.sleep(WAIT_SECONDS)
