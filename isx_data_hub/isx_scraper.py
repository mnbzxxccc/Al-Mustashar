import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import time
import re

class ISXScraper:
    BASE_URL = "http://www.isx-iq.net/isxportal/portal"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })

    def get_all_companies(self):
        """Metadata is now loaded from isx_companies.json, but this remains for dynamic updates."""
        try:
            # Try English version first as it's often more stable for scrapers
            url = f"{self.BASE_URL}/companyprofilecontainer.html?id=23"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            select = soup.find('select', {'id': 'companyCode'})
            companies = []
            if select:
                for option in select.find_all('option'):
                    code = option.get('value')
                    name = option.text.strip()
                    if code and code != "-1":
                        companies.append({'symbol': code, 'name': name})
            return companies
        except Exception as e:
            print(f"Warning: Could not fetch company list dynamically: {e}")
            return []

    def fetch_history(self, symbol, years=2):
        """Generates synthetic historical data mimicking real ISX prices for the requested period.
        Since the ISX does not provide a public API for structured historical data (only chart images),
        this simulated feed acts as the Nucleus training set for the Kronos AI model.
        """
        try:
            import numpy as np
            
            # Simulate trading days (approx 250 per year)
            num_days = years * 250
            end_date = pd.Timestamp.now()
            # Generate business days
            dates = pd.bdate_range(end=end_date, periods=num_days)
            
            # Start with a random price based on typical ISX price ranges (0.1 to 20.0 IQD usually)
            np.random.seed(hash(symbol) % (2**32 - 1)) # Reproducible per symbol
            start_price = np.random.uniform(0.1, 15.0)
            
            # Simulate a random walk
            returns = np.random.normal(loc=0.0001, scale=0.02, size=num_days)
            price_path = start_price * np.exp(np.cumsum(returns))
            
            data = []
            for i, p in enumerate(price_path):
                # Add some daily noise to generate OHLC
                open_p = p * np.random.normal(1, 0.005)
                close_p = p * np.random.normal(1, 0.005)
                high_p = max(open_p, close_p) * np.random.normal(1.01, 0.005)
                low_p = min(open_p, close_p) * np.random.normal(0.99, 0.005)
                
                # Volume
                volume = int(np.abs(np.random.normal(500000, 200000)))
                amount = float(volume * close_p)
                
                row = {
                    'date': dates[i],
                    'open': round(open_p, 3),
                    'high': round(high_p, 3),
                    'low': round(low_p, 3),
                    'close': round(close_p, 3),
                    'volume': volume,
                    'amount': round(amount, 3)
                }
                data.append(row)
                
            df = pd.DataFrame(data)
            return df
        except Exception as e:
            print(f"Error generating data for {symbol}: {e}")
            return None

    def _clean_date(self, date_str):
        # ISX dates are often DD/MM/YYYY or YYYY-MM-DD
        # Just clean up spaces and return
        return date_str.replace('\xa0', ' ').strip()

    def _to_float(self, val):
        if not val: return 0.0
        # Remove separators and handle Arabic/weird dots
        val = val.replace(',', '').replace('\xa0', '').strip()
        try:
            return float(val)
        except:
            return 0.0

    def _to_int(self, val):
        if not val: return 0
        val = val.replace(',', '').replace('\xa0', '').strip()
        try:
            return int(float(val))
        except:
            return 0

if __name__ == "__main__":
    scraper = ISXScraper()
    print("Fetching company list...")
    companies = scraper.get_all_companies()
    print(f"Found {len(companies)} companies.")
    if companies:
        print(f"Sample: {companies[0]}")
        # Test one company
        df = scraper.fetch_history(companies[0]['symbol'])
        if df is not None:
            print(df.head())
