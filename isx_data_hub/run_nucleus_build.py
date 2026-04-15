import json
import os
import time
from isx_scraper import ISXScraper
from isx_manager import ISXManager

def main():
    scraper = ISXScraper()
    manager = ISXManager()
    
    # Load companies
    with open('isx_companies.json', 'r') as f:
        sectors = json.load(f)
    
    total_companies = sum(len(symbols) for symbols in sectors.values())
    print(f"Starting Nucleus Build for {total_companies} companies...")
    
    processed = 0
    errors = []
    
    for sector, symbols in sectors.items():
        print(f"\n--- Sector: {sector} ---")
        for symbol in symbols:
            processed += 1
            print(f"[{processed}/{total_companies}] Processing {symbol}...", end=" ", flush=True)
            
            try:
                # Save metadata
                company_id = manager.save_company(symbol, name=symbol, sector=sector)
                
                # Fetch history (last 2 years)
                df = scraper.fetch_history(symbol, years=2)
                
                if df is not None and not df.empty:
                    manager.save_prices(company_id, df)
                    print(f"Successfully saved {len(df)} rows.")
                else:
                    print("No data found.")
                    errors.append(symbol)
                
                # Sleep to avoid rate limiting
                time.sleep(1) 
                
            except Exception as e:
                print(f"Error: {e}")
                errors.append(symbol)
    
    print("\n--- Nucleus Build Complete ---")
    print(f"Total processed: {processed}")
    print(f"Errors: {len(errors)}")
    if errors:
        print(f"Symbols with errors: {', '.join(errors)}")
    
    print("\nGenerating Excel report...")
    manager.export_to_excel()
    print("Done.")

if __name__ == "__main__":
    main()
