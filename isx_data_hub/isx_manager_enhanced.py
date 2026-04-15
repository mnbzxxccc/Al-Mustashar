import sqlite3
import pandas as pd
import os

class ISXManagerEnhanced:
    DB_NAME = "isx_nucleus_enhanced.db"
    EXCEL_NAME = "isx_nucleus_enhanced.xlsx"
    
    def __init__(self, output_dir="."):
        # Resolve the directory based on the file location if needed
        # Fallback to output_dir
        self.output_dir = output_dir
        self.db_path = os.path.join(output_dir, self.DB_NAME)
        self.excel_path = os.path.join(output_dir, self.EXCEL_NAME)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # --- Existing Entities (Enhanced) ---
            # 1. Companies
            cursor.execute('''CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT UNIQUE, name TEXT, sector TEXT
            )''')
            
            # 2. Prices
            cursor.execute('''CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER,
                date DATE, open REAL, high REAL, low REAL, close REAL, volume INTEGER, amount REAL,
                UNIQUE(company_id, date), FOREIGN KEY (company_id) REFERENCES companies(id)
            )''')
            # Critical Index for quick history loads
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_prices_company_date ON prices(company_id, date)')
            
            # --- New Professional Entities ---
            
            # 3. Macro Factors
            cursor.execute('''CREATE TABLE IF NOT EXISTS macro_factors (
                date DATE PRIMARY KEY, oil_price_bbl REAL, usd_iqd_parallel REAL, cbi_rate REAL
            )''')

            # 4. Financial Statements (Fundamentals)
            cursor.execute('''CREATE TABLE IF NOT EXISTS financial_statements (
                id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, year INTEGER, quarter INTEGER,
                revenue REAL, net_income REAL, total_assets REAL, total_liabilities REAL, 
                total_equity REAL, operating_cash_flow REAL, free_cash_flow REAL, shares_outstanding INTEGER,
                UNIQUE(company_id, year, quarter), FOREIGN KEY (company_id) REFERENCES companies(id)
            )''')

            # 5. Financial Ratios (Auto Calculated)
            cursor.execute('''CREATE TABLE IF NOT EXISTS financial_ratios (
                id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, year INTEGER, quarter INTEGER,
                pe_ratio REAL, pb_ratio REAL, roe REAL, roa REAL, debt_to_equity REAL, current_ratio REAL,
                UNIQUE(company_id, year, quarter), FOREIGN KEY (company_id) REFERENCES companies(id)
            )''')
            
            # 6. Technical Indicators (Computed)
            cursor.execute('''CREATE TABLE IF NOT EXISTS technical_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, date DATE,
                rsi_14 REAL, macd_hist REAL, bollinger_upper REAL, bollinger_lower REAL,
                sma_50 REAL, sma_200 REAL,
                UNIQUE(company_id, date), FOREIGN KEY (company_id) REFERENCES companies(id)
            )''')

            # 7. Dividends
            cursor.execute('''CREATE TABLE IF NOT EXISTS dividends (
                id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER,
                ex_dividend_date DATE, amount_per_share REAL, dividend_yield REAL,
                UNIQUE(company_id, ex_dividend_date), FOREIGN KEY (company_id) REFERENCES companies(id)
            )''')
            
            # 8, 9, 10. AI & RAG Data
            cursor.execute('''CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER,
                date DATE, headline TEXT, content TEXT, FOREIGN KEY (company_id) REFERENCES companies(id)
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS stakeholders (
                id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER,
                owner_name TEXT, share_percentage REAL, FOREIGN KEY (company_id) REFERENCES companies(id)
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS ai_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER,
                prediction_date DATE, target_date DATE, predicted_close REAL, confidence_score REAL,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )''')
            
            conn.commit()

    def save_financial_statement(self, company_id, year, quarter, data):
        """Save raw financial data and auto-calculate key investment ratios."""
        with sqlite3.connect(self.db_path) as conn:
            # Save Raw Statement
            conn.execute('''
                INSERT OR REPLACE INTO financial_statements 
                (company_id, year, quarter, revenue, net_income, total_assets, total_liabilities, total_equity, operating_cash_flow, free_cash_flow, shares_outstanding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (company_id, year, quarter, data.get('revenue'), data.get('net_income'), 
                  data.get('total_assets'), data.get('total_liabilities'), data.get('total_equity'),
                  data.get('operating_cash_flow'), data.get('free_cash_flow'), data.get('shares_outstanding')))
            
            # --- Auto Calculate Advanced Ratios ---
            roe = None
            if data.get('total_equity') and data.get('total_equity') > 0 and data.get('net_income') is not None:
                roe = (data.get('net_income', 0) / data.get('total_equity')) * 100
                
            roa = None
            if data.get('total_assets') and data.get('total_assets') > 0 and data.get('net_income') is not None:
                roa = (data.get('net_income', 0) / data.get('total_assets')) * 100
                
            debt_to_equity = None
            if data.get('total_equity') and data.get('total_equity') > 0 and data.get('total_liabilities') is not None:
                debt_to_equity = data.get('total_liabilities', 0) / data.get('total_equity')
                
            conn.execute('''
                INSERT OR REPLACE INTO financial_ratios (company_id, year, quarter, roe, roa, debt_to_equity)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (company_id, year, quarter, roe, roa, debt_to_equity))
            conn.commit()

    def get_latest_financials(self, company_id):
        """Returns the most up-to-date fundamental analysis profile for AI/UI."""
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query('''
                SELECT * FROM financial_statements fs 
                LEFT JOIN financial_ratios fr ON fs.company_id = fr.company_id AND fs.year = fr.year AND fs.quarter = fr.quarter
                WHERE fs.company_id = ? ORDER BY fs.year DESC, fs.quarter DESC LIMIT 1
            ''', conn, params=(company_id,))
            return df.iloc[0].to_dict() if not df.empty else None

if __name__ == "__main__":
    manager = ISXManagerEnhanced()
    print("✨ ISX Nucleus Enhanced Initialized Successfully.")
