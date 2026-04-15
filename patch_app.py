import os

file_path = r"e:\Kronos-master\webui\app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add imports at the top
import_statement = """import warnings
import datetime
warnings.filterwarnings('ignore')

from plotly.subplots import make_subplots
from financial_rationale import generate_financial_rationale
from indicators import calculate_bollinger_bands, calculate_macd, calculate_rsi, calculate_mfi, calculate_sharpe_ratio, calculate_confidence_score, generate_sentiment_analysis
"""
content = content.replace("import warnings\nimport datetime\nwarnings.filterwarnings('ignore')", import_statement, 1)
content = content.replace("from financial_rationale import generate_financial_rationale\n", "", 1) # remove previous if exists

# 2. Rewrite create_prediction_chart
chart_function_start = "def create_prediction_chart(df, pred_df, lookback, pred_len, actual_df=None, historical_start_idx=0):"
chart_function_end = "    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)"

# Find start and end indices
start_idx = content.find(chart_function_start)
end_idx = content.find(chart_function_end, start_idx) + len(chart_function_end)

new_chart_function = """def create_prediction_chart(df, pred_df, lookback, pred_len, actual_df=None, historical_start_idx=0):
    \"\"\"Create prediction chart with Dark Mode and Subplots\"\"\"
    if historical_start_idx + lookback + pred_len <= len(df):
        historical_df = df.iloc[historical_start_idx:historical_start_idx+lookback].copy()
    else:
        av_lb = min(lookback, len(df) - historical_start_idx)
        historical_df = df.iloc[historical_start_idx:historical_start_idx+av_lb].copy()
    
    # Calculate Bollinger Bands on Historical
    hist_bb_upper, hist_bb_mid, hist_bb_lower = calculate_bollinger_bands(historical_df['close'])
    macd_line, macd_signal, macd_hist = calculate_macd(historical_df['close'])
    rsi = calculate_rsi(historical_df['close'])
    
    # We need timestamps
    if 'timestamps' in historical_df.columns:
        hist_time = historical_df['timestamps']
    else:
        hist_time = historical_df.index
        
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=("Price & Bollinger Bands", "MACD", "RSI")
    )
    
    # Upper Band
    fig.add_trace(go.Scatter(x=hist_time, y=hist_bb_upper, mode='lines', line=dict(color='rgba(173,216,230,0.4)', width=1), name='Upper BB'), row=1, col=1)
    # Lower Band
    fig.add_trace(go.Scatter(x=hist_time, y=hist_bb_lower, mode='lines', line=dict(color='rgba(173,216,230,0.4)', width=1), fill='tonexty', fillcolor='rgba(173,216,230,0.1)', name='Lower BB'), row=1, col=1)
    
    # Historical Candles
    fig.add_trace(go.Candlestick(
        x=hist_time, open=historical_df['open'], high=historical_df['high'], low=historical_df['low'], close=historical_df['close'],
        name='Historical Data', increasing_line_color='#26A69A', decreasing_line_color='#EF5350'
    ), row=1, col=1)
    
    # Prediction Candles
    is_multi = isinstance(pred_df, dict)
    pred_data = pred_df["avg"] if is_multi else pred_df
    
    if pred_data is not None and len(pred_data) > 0:
        if 'timestamps' in df.columns and len(historical_df) > 0:
            last_time = historical_df['timestamps'].iloc[-1]
            t_diff = df['timestamps'].iloc[1] - df['timestamps'].iloc[0] if len(df) > 1 else pd.Timedelta(hours=1)
            pred_time = pd.date_range(start=last_time + t_diff, periods=len(pred_data), freq=t_diff)
        else:
            pred_time = range(len(historical_df), len(historical_df) + len(pred_data))
            
        if is_multi:
            fig.add_trace(go.Scatter(x=pred_time, y=pred_df["best"]["close"], mode='lines', name='Best Path', line=dict(color='rgba(102, 187, 106, 0.8)', width=2, dash='dot')), row=1, col=1)
            fig.add_trace(go.Scatter(x=pred_time, y=pred_df["worst"]["close"], mode='lines', name='Worst Path', line=dict(color='rgba(239, 83, 80, 0.8)', width=2, dash='dot')), row=1, col=1)
            
        fig.add_trace(go.Candlestick(
            x=pred_time, open=pred_data['open'], high=pred_data['high'], low=pred_data['low'], close=pred_data['close'],
            name='Expected Forecast', increasing_line_color='#66BB6A', decreasing_line_color='#FF7043'
        ), row=1, col=1)
        
    # MACD Plot
    fig.add_trace(go.Scatter(x=hist_time, y=macd_line, mode='lines', name='MACD', line=dict(color='#2962FF')), row=2, col=1)
    fig.add_trace(go.Scatter(x=hist_time, y=macd_signal, mode='lines', name='Signal', line=dict(color='#FF6D00')), row=2, col=1)
    colors = ['#26A69A' if val >= 0 else '#EF5350' for val in macd_hist]
    fig.add_trace(go.Bar(x=hist_time, y=macd_hist, name='MACD Hist', marker_color=colors), row=2, col=1)
    
    # RSI Plot
    fig.add_trace(go.Scatter(x=hist_time, y=rsi, mode='lines', name='RSI', line=dict(color='#AB47BC')), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    
    fig.update_layout(
        title='Kronos ISX Intelligence Hub - Advanced Technical Analysis',
        template='plotly_dark',
        height=800,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=False,
        xaxis3_rangeslider_visible=False
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)"""

content = content[:start_idx] + new_chart_function + content[end_idx:]

# 3. Update the prediction response structure to include Confidence and Sentiment
old_response = """        # Generate Rationale
        is_multi = isinstance(pred_df, dict)
        pred_df_avg = pred_df["avg"] if is_multi else pred_df
        rationale_text = generate_financial_rationale(x_df, pred_df_avg)"""

new_response = """        # Generate Rationale and Indicators
        is_multi = isinstance(pred_df, dict)
        pred_df_avg = pred_df["avg"] if is_multi else pred_df
        
        current_price = x_df['close'].values[-1]
        rationale_text = generate_financial_rationale(x_df, pred_df_avg)
        
        mfi_val = calculate_mfi(x_df).values[-1]
        _, _, macd_hist = calculate_macd(x_df['close'])
        macd_val = macd_hist.values[-1]
        
        sentiment = generate_sentiment_analysis(mfi_val, macd_val)
        confidence = calculate_confidence_score(pred_df, current_price)
        sharpe = calculate_sharpe_ratio(x_df['close'])"""

content = content.replace(old_response, new_response)

old_jsonify = """        return jsonify({
            'success': True,
            'prediction_type': prediction_type,
            'chart': chart_json,
            'rationale': rationale_text,
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
            'prediction_results': prediction_results,
            'actual_data': actual_data,
            'has_comparison': len(actual_data) > 0,
            'message': f'Prediction completed successfully.'
        })"""

content = content.replace(old_jsonify, new_jsonify)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("app.py successfully updated.")
