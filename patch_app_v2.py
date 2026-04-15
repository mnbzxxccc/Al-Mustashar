import os

file_path = r"e:\Kronos-master\webui\app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Imports
new_imports = """from indicators import calculate_bollinger_bands, calculate_macd, calculate_rsi, calculate_mfi, calculate_sharpe_ratio, calculate_confidence_score, generate_sentiment_analysis
from risk_engine import calculate_garch_volatility, calculate_sortino_ratio, detect_liquidity_gaps, simulate_currency_impact
from portfolio_optimizer import optimize_portfolio, get_correlation_matrix
"""
content = content.replace("from indicators import calculate_bollinger_bands, calculate_macd, calculate_rsi, calculate_mfi, calculate_sharpe_ratio, calculate_confidence_score, generate_sentiment_analysis", new_imports)

# 2. Update the predict function response building
old_stats = """        sentiment = generate_sentiment_analysis(mfi_val, macd_val)
        confidence = calculate_confidence_score(pred_df, current_price)
        sharpe = calculate_sharpe_ratio(x_df['close'])"""

new_stats = """        sentiment = generate_sentiment_analysis(mfi_val, macd_val)
        confidence = calculate_confidence_score(pred_df, current_price)
        sharpe = calculate_sharpe_ratio(x_df['close'])
        
        # Phase 2: Risk Metrics
        returns = x_df['close'].pct_change().dropna()
        garch_vol = calculate_garch_volatility(returns)
        sortino = calculate_sortino_ratio(x_df['close'])
        liquidity_gaps = detect_liquidity_gaps(x_df)"""

content = content.replace(old_stats, new_stats)

old_jsonify = """        return jsonify({
            'success': True,
            'prediction_type': prediction_type,
            'chart': chart_json,
            'rationale': rationale_text,
            'sentiment': sentiment,
            'confidence': confidence,
            'sharpe': f"{sharpe:.2f}",
            'prediction_results': prediction_results,
            'actual_data': actual_data,
            'has_comparison': len(actual_data) > 0,
            'message': f'Prediction completed successfully.'
        })"""

new_jsonify = """        return jsonify({
            'success': True,
            'prediction_type': prediction_type,
            'chart': chart_json,
            'rationale': rationale_text,
            'sentiment': sentiment,
            'confidence': confidence,
            'sharpe': f"{sharpe:.2f}",
            'garch_vol': f"{garch_vol*100:.2f}%" if garch_vol else "N/A",
            'sortino': f"{sortino:.2f}",
            'liquidity_gaps': liquidity_gaps,
            'prediction_results': prediction_results,
            'actual_data': actual_data,
            'has_comparison': len(actual_data) > 0,
            'message': f'Prediction completed successfully.'
        })"""

content = content.replace(old_jsonify, new_jsonify)

# 3. Add Portfolio Routes
portfolio_routes = """
@app.route('/portfolio')
def portfolio_lab():
    \"\"\"Portfolio Lab page\"\"\"
    return render_template('portfolio.html')

@app.route('/api/portfolio/optimize', methods=['POST'])
def api_optimize_portfolio():
    data = request.json
    symbols = data.get('symbols', [])
    result = optimize_portfolio(symbols)
    return jsonify(result)

@app.route('/api/portfolio/correlation', methods=['POST'])
def api_correlation_matrix():
    data = request.json
    symbols = data.get('symbols', [])
    result = get_correlation_matrix(symbols)
    return jsonify(result)
"""

# Append before if __name__ == '__main__':
content = content.replace("if __name__ == '__main__':", portfolio_routes + "\nif __name__ == '__main__':")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("app.py successfully updated for Phase 2.")
