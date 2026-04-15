import sqlite3
import os

class AnalysisEngine:
    """
    Intelligent Analysis Engine that combines Fundamentals, Technicals, and Macro Factors
    to provide institutional grade recommendations.
    """
    def __init__(self, db_name="isx_nucleus_enhanced.db"):
        # Resolve path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(current_dir, db_name)
        
    def generate_investment_recommendation(self, company_id, company_symbol, latest_year=None, latest_quarter=None):
        score = 0
        reasons = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 1. Fundamental Level (Financials & Ratios)
                cursor.execute('''
                    SELECT * FROM financial_ratios 
                    WHERE company_id = ? 
                    ORDER BY year DESC, quarter DESC LIMIT 1
                ''', (company_id,))
                ratios = cursor.fetchone()
                
                if ratios:
                    roe = ratios['roe']
                    debt_eq = ratios['debt_to_equity']
                    
                    if roe and roe > 15:
                        score += 2
                        reasons.append(f"🟢 ربحية قوية (ROE={roe:.1f}%)")
                    elif roe and roe < 0:
                        score -= 2
                        reasons.append(f"🔴 عوائد سلبية (ROE={roe:.1f}%)")
                        
                    if debt_eq is not None:
                        if debt_eq < 0.5:
                            score += 1
                            reasons.append("🟢 ميزانية صحية (ديون منخفضة)")
                        elif debt_eq > 2:
                            score -= 1
                            reasons.append("🔴 مخاطر ديون عالية جداً")
                else:
                    reasons.append("⚪ بيانات الميزانية الأساسية غير متوفرة")
                
                # 2. Technical Level
                cursor.execute('''
                    SELECT * FROM technical_indicators 
                    WHERE company_id = ? ORDER BY date DESC LIMIT 1
                ''', (company_id,))
                techs = cursor.fetchone()
                
                if techs:
                    rsi = techs['rsi_14']
                    if rsi:
                        if rsi < 30:
                            score += 1
                            reasons.append("🟢 تشبع بيعي فنياً (RSI<30) - فرصة للاقتناص")
                        elif rsi > 70:
                            score -= 1
                            reasons.append("🔴 تشبع شرائي فنياً (RSI>70) - توقع تصحيح قريب")
                
                # 3. Macro Level (Oil impact on Iraq Market)
                cursor.execute('SELECT oil_price_bbl FROM macro_factors ORDER BY date DESC LIMIT 1')
                macro = cursor.fetchone()
                if macro and macro['oil_price_bbl']:
                    oil = macro['oil_price_bbl']
                    if oil > 80:
                        score += 1
                        reasons.append(f"🟢 بيئة داعمة للاقتصاد (سعر النفط {oil}$) يدعم النمو")
                    elif oil < 60:
                        score -= 1
                        reasons.append(f"🔴 ضغوط على الاقتصاد (النفط {oil}$) قد يقلل الإنفاق الحكومي")
                
        except Exception as e:
            return {"error": str(e), "recommendation": "UNKNOWN", "score": 0, "reasons": ["Error mapping database."]}
            
        # Determine Final Output
        if score >= 3:
            rec = "🟢 STRONG BUY"
        elif score >= 1:
            rec = "🟡 BUY"
        elif score >= -1:
            rec = "⚪ HOLD"
        elif score >= -3:
            rec = "🟠 SELL"
        else:
            rec = "🔴 STRONG SELL"
            
        return {
            "symbol": company_symbol,
            "overall_score": score,
            "recommendation": rec,
            "reasons": reasons
        }

if __name__ == "__main__":
    # Quick Test Execution
    engine = AnalysisEngine()
    print("🤖 Analysis Engine Ready for Institutional Execution.")
