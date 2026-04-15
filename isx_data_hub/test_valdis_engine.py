import sys
import os
import sqlite3

# Ensure we can import from the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from isx_manager_enhanced import ISXManagerEnhanced
from analysis_engine import AnalysisEngine

def main():
    print("🚀 Initializing ISX Manager...")
    manager = ISXManagerEnhanced(output_dir=current_dir)
    
    print("🌱 Seeding Database with Simulator Data...")
    with sqlite3.connect(manager.db_path) as conn:
        c = conn.cursor()
        companies = [
            ('ABK', 'Al-Ahly Bank', 'Banking'),
            ('BOP', 'Bank of Baghdad', 'Banking'),
            ('IIC', 'Iraqi Insurance', 'Insurance'),
            ('KPI', 'Kurdistan Pipeline', 'Energy'),
            ('TASC', 'Asiacell', 'Telecom')
        ]
        
        for sym, name, sec in companies:
            c.execute('INSERT OR IGNORE INTO companies (symbol, name, sector) VALUES (?, ?, ?)', (sym, name, sec))
            
        c.execute('SELECT id, symbol FROM companies')
        comp_map = {row[1]: row[0] for row in c.fetchall()}
        
        # Inject Macro Factor (Favorable Oil Price)
        c.execute('INSERT OR REPLACE INTO macro_factors (date, oil_price_bbl) VALUES ("2024-03-01", 85.5)')
        conn.commit()

    # --- Seed Fundamentals ---
    # ABK: Excellent (Low Debt, High ROE) 
    manager.save_financial_statement(comp_map['ABK'], 2024, 1, 
        {'revenue': 50000, 'net_income': 25000, 'total_assets': 200000, 'total_liabilities': 20000, 'total_equity': 180000})

    # BOP: Good/Moderate
    manager.save_financial_statement(comp_map['BOP'], 2024, 1, 
        {'revenue': 40000, 'net_income': 8000, 'total_assets': 100000, 'total_liabilities': 60000, 'total_equity': 40000})

    # KPI: Bad (Negative income, High debt)
    manager.save_financial_statement(comp_map['KPI'], 2024, 1, 
        {'revenue': 20000, 'net_income': -5000, 'total_assets': 80000, 'total_liabilities': 60000, 'total_equity': 20000})

    # --- Seed Technicals ---
    with sqlite3.connect(manager.db_path) as conn:
        c = conn.cursor()
        # ABK is Undervalued (RSI 25)
        c.execute('INSERT OR REPLACE INTO technical_indicators (company_id, date, rsi_14) VALUES (?, "2024-03-01", 25)', (comp_map['ABK'],))
        # KPI is Overvalued (RSI 80)
        c.execute('INSERT OR REPLACE INTO technical_indicators (company_id, date, rsi_14) VALUES (?, "2024-03-01", 80)', (comp_map['KPI'],))
        conn.commit()

    # --- Run Analysis Engine ---
    print("\n🧠 Valdis AI Engine - Running Multi-Factor Analysis...")
    engine = AnalysisEngine(db_name="isx_nucleus_enhanced.db")
    results = []
    
    for sym, cid in comp_map.items():
        res = engine.generate_investment_recommendation(cid, sym)
        if res and "reasons" in res:
            results.append(res)
            
    # Sort by recommendation score (highest first)
    results.sort(key=lambda x: x.get('overall_score', -99), reverse=True)
    
    print("=" * 60)
    print("   📊 TOP STOCKS RECOMMENDATION (Valdis Report)   ")
    print("=" * 60)
    for r in results:
        print(f"\n🏢 {r['symbol']} | REC: {r['recommendation']} | Score: {r['overall_score']}")
        for reason in r['reasons']:
            print(f"   {reason}")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
