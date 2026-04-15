import os
import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go
import plotly.utils
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sqlite3
import sys
import datetime
from dotenv import load_dotenv

# Load environment variables from .env file (parent directory)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

warnings.filterwarnings('ignore')

from plotly.subplots import make_subplots
from core_analytics.indicators import calculate_bollinger_bands, calculate_macd, calculate_rsi, calculate_mfi, calculate_sharpe_ratio, calculate_confidence_score, generate_sentiment_analysis
from core_analytics.risk_engine import calculate_garch_volatility, calculate_sortino_ratio, detect_liquidity_gaps, simulate_currency_impact
from core_analytics.portfolio_optimizer import optimize_portfolio, get_correlation_matrix
from core_analytics.financial_rationale import generate_financial_rationale

# Configuration from Environment Variables
DB_PATH = os.getenv("DATABASE_PATH", r"E:\Kronos-master\isx_data_hub\isx_nucleus_enhanced.db")
PORT = int(os.getenv("PORT", 7070))
DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"

# Centralized Analysis Engine
from isx_data_hub.analysis_engine import AnalysisEngine
analysis_engine = AnalysisEngine(db_name="isx_nucleus_enhanced.db")

# Add project root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from model import Kronos, KronosTokenizer, KronosPredictor
    MODEL_AVAILABLE = True
except ImportError:
    MODEL_AVAILABLE = False
    print("Warning: Kronos model cannot be imported, will use simulated data for demonstration")

app = Flask(__name__)
CORS(app)

# Global variables to store models
tokenizer = None
model = None
predictor = None

# Available model configurations
AVAILABLE_MODELS = {
    'kronos-mini': {
        'name': 'Kronos-mini',
        'model_id': 'NeoQuasar/Kronos-mini',
        'tokenizer_id': 'NeoQuasar/Kronos-Tokenizer-2k',
        'context_length': 2048,
        'params': '4.1M',
        'description': 'Lightweight model, suitable for fast prediction'
    },
    'kronos-small': {
        'name': 'Kronos-small',
        'model_id': 'NeoQuasar/Kronos-small',
        'tokenizer_id': 'NeoQuasar/Kronos-Tokenizer-base',
        'context_length': 512,
        'params': '24.7M',
        'description': 'Small model, balanced performance and speed'
    },
    'kronos-base': {
        'name': 'Kronos-base',
        'model_id': 'NeoQuasar/Kronos-base',
        'tokenizer_id': 'NeoQuasar/Kronos-Tokenizer-base',
        'context_length': 512,
        'params': '102.3M',
        'description': 'Base model, provides better prediction quality'
    }
}

def load_data_files():
    """Scan data directory and return available data files"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    data_files = []
    
    if os.path.exists(data_dir):
        for file in os.listdir(data_dir):
            if file.endswith(('.csv', '.feather')):
                file_path = os.path.join(data_dir, file)
                file_size = os.path.getsize(file_path)
                data_files.append({
                    'name': file,
                    'path': file_path,
                    'size': f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"
                })
    
    return data_files

def load_data_file(file_path):
    """Load data file"""
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.feather'):
            df = pd.read_feather(file_path)
        else:
            return None, "Unsupported file format"
        
        # Check required columns
        required_cols = ['open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            return None, f"Missing required columns: {required_cols}"
        
        # Process timestamp column
        if 'timestamps' in df.columns:
            df['timestamps'] = pd.to_datetime(df['timestamps'])
        elif 'timestamp' in df.columns:
            df['timestamps'] = pd.to_datetime(df['timestamp'])
        elif 'date' in df.columns:
            # If column name is 'date', rename it to 'timestamps'
            df['timestamps'] = pd.to_datetime(df['date'])
        else:
            # If no timestamp column exists, create one
            df['timestamps'] = pd.date_range(start='2024-01-01', periods=len(df), freq='1H')
        
        # Ensure numeric columns are numeric type
        for col in ['open', 'high', 'low', 'close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Process volume column (optional)
        if 'volume' in df.columns:
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        # Process amount column (optional, but not used for prediction)
        if 'amount' in df.columns:
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        # Remove rows containing NaN values
        df = df.dropna()
        
        return df, None
        
    except Exception as e:
        return None, f"Failed to load file: {str(e)}"

def load_isx_data(symbol):
    """Load data from ISX SQLite Nucleus database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        query = '''
            SELECT p.date as timestamps, p.open, p.high, p.low, p.close, p.volume
            FROM prices p
            JOIN companies c ON p.company_id = c.id
            WHERE c.symbol = ?
            ORDER BY p.date ASC
        '''
        df = pd.read_sql_query(query, conn, params=(symbol,))
        conn.close()
        
        if df.empty:
            return None, f"No data found for symbol {symbol}"
            
        df['timestamps'] = pd.to_datetime(df['timestamps'])
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna()
        return df, None
    except Exception as e:
        return None, f"Failed to load ISX data: {str(e)}"

def save_prediction_results(file_path, prediction_type, prediction_results, actual_data, input_data, prediction_params):
    """Save prediction results to file"""
    try:
        # Create prediction results directory
        results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prediction_results')
        os.makedirs(results_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'prediction_{timestamp}.json'
        filepath = os.path.join(results_dir, filename)
        
        # Prepare data for saving
        save_data = {
            'timestamp': datetime.datetime.now().isoformat(),
            'file_path': file_path,
            'prediction_type': prediction_type,
            'prediction_params': prediction_params,
            'input_data_summary': {
                'rows': len(input_data),
                'columns': list(input_data.columns),
                'price_range': {
                    'open': {'min': float(input_data['open'].min()), 'max': float(input_data['open'].max())},
                    'high': {'min': float(input_data['high'].min()), 'max': float(input_data['high'].max())},
                    'low': {'min': float(input_data['low'].min()), 'max': float(input_data['low'].max())},
                    'close': {'min': float(input_data['close'].min()), 'max': float(input_data['close'].max())}
                },
                'last_values': {
                    'open': float(input_data['open'].iloc[-1]),
                    'high': float(input_data['high'].iloc[-1]),
                    'low': float(input_data['low'].iloc[-1]),
                    'close': float(input_data['close'].iloc[-1])
                }
            },
            'prediction_results': prediction_results,
            'actual_data': actual_data,
            'analysis': {}
        }
        
        # If actual data exists, perform comparison analysis
        if actual_data and len(actual_data) > 0:
            # Calculate continuity analysis
            if len(prediction_results) > 0 and len(actual_data) > 0:
                last_pred = prediction_results[0]  # First prediction point
            first_actual = actual_data[0]      # First actual point
                
            save_data['analysis']['continuity'] = {
                    'last_prediction': {
                        'open': last_pred['open'],
                        'high': last_pred['high'],
                        'low': last_pred['low'],
                        'close': last_pred['close']
                    },
                    'first_actual': {
                        'open': first_actual['open'],
                        'high': first_actual['high'],
                        'low': first_actual['low'],
                        'close': first_actual['close']
                    },
                    'gaps': {
                        'open_gap': abs(last_pred['open'] - first_actual['open']),
                        'high_gap': abs(last_pred['high'] - first_actual['high']),
                        'low_gap': abs(last_pred['low'] - first_actual['low']),
                        'close_gap': abs(last_pred['close'] - first_actual['close'])
                    },
                    'gap_percentages': {
                        'open_gap_pct': (abs(last_pred['open'] - first_actual['open']) / first_actual['open']) * 100,
                        'high_gap_pct': (abs(last_pred['high'] - first_actual['high']) / first_actual['high']) * 100,
                        'low_gap_pct': (abs(last_pred['low'] - first_actual['low']) / first_actual['low']) * 100,
                        'close_gap_pct': (abs(last_pred['close'] - first_actual['close']) / first_actual['close']) * 100
                    }
                }
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        print(f"Prediction results saved to: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"Failed to save prediction results: {e}")
        return None

def create_prediction_chart(df, pred_df, lookback, pred_len, actual_df=None, historical_start_idx=0):
    """Create prediction chart with Dark Mode and Subplots"""
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
        title='Valdis Intelligence Hub — Advanced Technical Analysis',
        template='plotly_dark',
        height=800,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=False,
        xaxis3_rangeslider_visible=False
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/api/isx-companies')
def get_isx_companies():
    """Get available ISX companies"""
    try:
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT symbol, name, sector FROM companies ORDER BY symbol"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return jsonify(df.to_dict('records'))
    except Exception as e:
        print(f"Error fetching ISX companies: {e}")
        return jsonify([])

@app.route('/api/data-files')
def get_data_files():
    """Get available data file list"""
    data_files = load_data_files()
    return jsonify(data_files)

@app.route('/api/load-data', methods=['POST'])
def load_data():
    """Load data file or ISX data"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        symbol = data.get('symbol')
        
        if symbol:
            df, error = load_isx_data(symbol)
        elif file_path:
            df, error = load_data_file(file_path)
        else:
            return jsonify({'error': 'Must provide symbol or file_path'}), 400
            
        if error:
            return jsonify({'error': error}), 400
        
        # Detect data time frequency
        def detect_timeframe(df):
            if len(df) < 2:
                return "Unknown"
            
            time_diffs = []
            for i in range(1, min(10, len(df))):  # Check first 10 time differences
                diff = df['timestamps'].iloc[i] - df['timestamps'].iloc[i-1]
                time_diffs.append(diff)
            
            if not time_diffs:
                return "Unknown"
            
            # Calculate average time difference
            avg_diff = sum(time_diffs, pd.Timedelta(0)) / len(time_diffs)
            
            # Convert to readable format
            if avg_diff < pd.Timedelta(minutes=1):
                return f"{avg_diff.total_seconds():.0f} seconds"
            elif avg_diff < pd.Timedelta(hours=1):
                return f"{avg_diff.total_seconds() / 60:.0f} minutes"
            elif avg_diff < pd.Timedelta(days=1):
                return f"{avg_diff.total_seconds() / 3600:.0f} hours"
            else:
                return f"{avg_diff.days} days"
        
        # Return data information
        data_info = {
            'rows': len(df),
            'columns': list(df.columns),
            'start_date': df['timestamps'].min().isoformat() if 'timestamps' in df.columns else 'N/A',
            'end_date': df['timestamps'].max().isoformat() if 'timestamps' in df.columns else 'N/A',
            'price_range': {
                'min': float(df[['open', 'high', 'low', 'close']].min().min()),
                'max': float(df[['open', 'high', 'low', 'close']].max().max())
            },
            'prediction_columns': ['open', 'high', 'low', 'close'] + (['volume'] if 'volume' in df.columns else []),
            'timeframe': detect_timeframe(df)
        }
        
        return jsonify({
            'success': True,
            'data_info': data_info,
            'message': f'Successfully loaded data, total {len(df)} rows'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to load data: {str(e)}'}), 500

@app.route('/api/predict', methods=['POST'])
def predict():
    """Perform prediction"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        symbol = data.get('symbol')
        lookback = int(data.get('lookback', 400))
        pred_len = int(data.get('pred_len', 120))
        
        # Get prediction quality parameters
        temperature = float(data.get('temperature', 1.0))
        top_p = float(data.get('top_p', 0.9))
        sample_count = int(data.get('sample_count', 1))
        
        if symbol:
            df, error = load_isx_data(symbol)
            source_name = symbol
        elif file_path:
            df, error = load_data_file(file_path)
            source_name = file_path
        else:
            return jsonify({'error': 'Must provide symbol or file_path'}), 400
        
        if error:
            return jsonify({'error': error}), 400
        
        if len(df) < lookback:
            return jsonify({'error': f'Insufficient data length, need at least {lookback} rows'}), 400
        
        # Perform prediction
        if MODEL_AVAILABLE and predictor is not None:
            try:
                # Use real Kronos model
                # Only use necessary columns: OHLCV, excluding amount
                required_cols = ['open', 'high', 'low', 'close']
                if 'volume' in df.columns:
                    required_cols.append('volume')
                
                # Process time period selection
                start_date = data.get('start_date')
                
                if start_date:
                    # Custom time period - fix logic: use data within selected window
                    start_dt = pd.to_datetime(start_date)
                    
                    # Find data after start time
                    mask = df['timestamps'] >= start_dt
                    time_range_df = df[mask]
                    
                    # Ensure sufficient data: lookback + pred_len
                    if len(time_range_df) < lookback + pred_len:
                        return jsonify({'error': f'Insufficient data from start time {start_dt.strftime("%Y-%m-%d %H:%M")}, need at least {lookback + pred_len} data points, currently only {len(time_range_df)} available'}), 400
                    
                    # Use first lookback data points within selected window for prediction
                    x_df = time_range_df.iloc[:lookback][required_cols]
                    x_timestamp = time_range_df.iloc[:lookback]['timestamps']
                    
                    # Use last pred_len data points within selected window as actual values
                    y_timestamp = time_range_df.iloc[lookback:lookback+pred_len]['timestamps']
                    
                    # Calculate actual time period length
                    start_timestamp = time_range_df['timestamps'].iloc[0]
                    end_timestamp = time_range_df['timestamps'].iloc[lookback+pred_len-1]
                    time_span = end_timestamp - start_timestamp
                    
                    prediction_type = f"Backtest mode (first {lookback} points, {pred_len} for comparison)"
                else:
                    # Forecast (Unknown Future) - take the LAST lookback points
                    if len(df) < lookback:
                        return jsonify({'error': f'Insufficient data, need {lookback} points.'}), 400
                    x_df = df.iloc[-lookback:][required_cols]
                    x_timestamp = df.iloc[-lookback:]['timestamps']
                    
                    time_diff = df['timestamps'].iloc[-1] - df['timestamps'].iloc[-2] if len(df) >= 2 else pd.Timedelta(hours=1)
                    y_timestamp = pd.date_range(start=df['timestamps'].iloc[-1] + time_diff, periods=pred_len, freq=time_diff)
                    
                    prediction_type = "Forecast Mode (Unknown Future)"
                
                # Ensure timestamps are Series format, not DatetimeIndex, to avoid .dt attribute error in Kronos model
                if isinstance(x_timestamp, pd.DatetimeIndex):
                    x_timestamp = pd.Series(x_timestamp, name='timestamps')
                if isinstance(y_timestamp, pd.DatetimeIndex):
                    y_timestamp = pd.Series(y_timestamp, name='timestamps')
                
                pred_df = predictor.predict(
                    df=x_df,
                    x_timestamp=x_timestamp,
                    y_timestamp=y_timestamp,
                    pred_len=pred_len,
                    T=temperature,
                    top_p=top_p,
                    sample_count=sample_count
                )
                
            except Exception as e:
                return jsonify({'error': f'Kronos model prediction failed: {str(e)}'}), 500
        else:
            return jsonify({'error': 'Kronos model not loaded, please load model first'}), 400
        
        # Prepare actual data for comparison (if exists)
        actual_data = []
        actual_df = None
        
        if start_date:  # Custom time period
            # Fix logic: use data within selected window
            # Prediction uses first 400 data points within selected window
            # Actual data should be last 120 data points within selected window
            start_dt = pd.to_datetime(start_date)
            
            # Find data starting from start_date
            mask = df['timestamps'] >= start_dt
            time_range_df = df[mask]
            
            if len(time_range_df) >= lookback + pred_len:
                # Get last 120 data points within selected window as actual values
                actual_df = time_range_df.iloc[lookback:lookback+pred_len]
                
                for i, (_, row) in enumerate(actual_df.iterrows()):
                    actual_data.append({
                        'timestamp': row['timestamps'].isoformat(),
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': float(row['volume']) if 'volume' in row else 0,
                    })
        else:  # Forecast Mode (no actual comparison data exists!)
            actual_df = None
            historical_start_idx = max(0, len(df) - lookback)
        
        # Generate Rationale and Indicators
        is_multi = isinstance(pred_df, dict)
        pred_df_avg = pred_df["avg"] if is_multi else pred_df
        
        current_price = x_df['close'].values[-1]
        rationale_text = generate_financial_rationale(x_df, pred_df_avg)
        
        mfi_val = calculate_mfi(x_df).values[-1]
        _, _, macd_hist = calculate_macd(x_df['close'])
        macd_val = macd_hist.values[-1]
        
        sentiment = generate_sentiment_analysis(mfi_val, macd_val)
        confidence = calculate_confidence_score(pred_df, current_price)
        sharpe = calculate_sharpe_ratio(x_df['close'])
        
        # Phase 2: Risk Metrics
        returns = x_df['close'].pct_change().dropna()
        garch_vol = calculate_garch_volatility(returns)
        sortino = calculate_sortino_ratio(x_df['close'])
        liquidity_gaps = detect_liquidity_gaps(x_df)
        
        # New: Phase 3 - Institutional Recommendation Engine
        # We need the company_id for the symbol
        conn = sqlite3.connect(DB_PATH)
        comp_info = pd.read_sql_query("SELECT id FROM companies WHERE symbol = ?", conn, params=(symbol,))
        conn.close()
        
        analysis_result = {"recommendation": "UNKNOWN", "reasons": []}
        if not comp_info.empty:
            comp_id = int(comp_info.iloc[0]['id'])
            analysis_result = analysis_engine.generate_investment_recommendation(comp_id, symbol)
            # Override sentiment text with professional recommendation if available
            sentiment = analysis_result['recommendation']
        
        # Create chart
        if start_date:
            start_dt = pd.to_datetime(start_date)
            mask = df['timestamps'] >= start_dt
            historical_start_idx = df[mask].index[0] if len(df[mask]) > 0 else 0
        else:
            historical_start_idx = max(0, len(df) - lookback)
        
        chart_json = create_prediction_chart(df, pred_df, lookback, pred_len, actual_df, historical_start_idx)
        
        # Prepare prediction result data - fix timestamp calculation logic
        if 'timestamps' in df.columns:
            if start_date:
                # Custom time period: use selected window data to calculate timestamps
                start_dt = pd.to_datetime(start_date)
                mask = df['timestamps'] >= start_dt
                time_range_df = df[mask]
                
                if len(time_range_df) >= lookback:
                    # Calculate prediction timestamps starting from last time point of selected window
                    last_timestamp = time_range_df['timestamps'].iloc[lookback-1]
                    time_diff = df['timestamps'].iloc[1] - df['timestamps'].iloc[0]
                    future_timestamps = pd.date_range(
                        start=last_timestamp + time_diff,
                        periods=pred_len,
                        freq=time_diff
                    )
                else:
                    future_timestamps = []
            else:
                # Latest data: calculate from last time point of entire data file
                last_timestamp = df['timestamps'].iloc[-1]
                time_diff = df['timestamps'].iloc[1] - df['timestamps'].iloc[0]
                future_timestamps = pd.date_range(
                    start=last_timestamp + time_diff,
                    periods=pred_len,
                    freq=time_diff
                )
        else:
            future_timestamps = range(len(df), len(df) + pred_len)
        
        prediction_results = []
        for i, (_, row) in enumerate(pred_df_avg.iterrows()):
            prediction_results.append({
                'timestamp': future_timestamps[i].isoformat() if i < len(future_timestamps) else f"T{i}",
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume']) if 'volume' in row else 0,
                'amount': float(row['amount']) if 'amount' in row else 0
            })
        
        try:
            save_prediction_results(
                file_path=source_name,
                prediction_type=prediction_type,
                prediction_results=prediction_results,
                actual_data=actual_data,
                input_data=x_df,
                prediction_params={
                    'lookback': lookback,
                    'pred_len': pred_len,
                    'temperature': temperature,
                    'top_p': top_p,
                    'sample_count': sample_count,
                    'start_date': start_date if start_date else 'latest'
                }
            )
        except Exception as e:
            print(f"Failed to save prediction results: {e}")
        
        return jsonify({
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
        })
        
    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

@app.route('/api/load-model', methods=['POST'])
def load_model():
    """Load Kronos model"""
    global tokenizer, model, predictor
    
    try:
        if not MODEL_AVAILABLE:
            return jsonify({'error': 'Kronos model library not available'}), 400
        
        data = request.get_json()
        model_key = data.get('model_key', 'kronos-small')
        device = data.get('device', 'cpu')
        
        if model_key not in AVAILABLE_MODELS:
            return jsonify({'error': f'Unsupported model: {model_key}'}), 400
        
        model_config = AVAILABLE_MODELS[model_key]
        
        # Load tokenizer and model
        tokenizer = KronosTokenizer.from_pretrained(model_config['tokenizer_id'])
        model = Kronos.from_pretrained(model_config['model_id'])
        
        # Create predictor
        predictor = KronosPredictor(model, tokenizer, device=device, max_context=model_config['context_length'])
        
        return jsonify({
            'success': True,
            'message': f'Model loaded successfully: {model_config["name"]} ({model_config["params"]}) on {device}',
            'model_info': {
                'name': model_config['name'],
                'params': model_config['params'],
                'context_length': model_config['context_length'],
                'description': model_config['description']
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Model loading failed: {str(e)}'}), 500

@app.route('/api/available-models')
def get_available_models():
    """Get available model list"""
    return jsonify({
        'models': AVAILABLE_MODELS,
        'model_available': MODEL_AVAILABLE
    })

@app.route('/api/model-status')
def get_model_status():
    """Get model status"""
    if MODEL_AVAILABLE:
        if predictor is not None:
            return jsonify({
                'available': True,
                'loaded': True,
                'message': 'Kronos model loaded and available',
                'current_model': {
                    'name': predictor.model.__class__.__name__,
                    'device': str(next(predictor.model.parameters()).device)
                }
            })
        else:
            return jsonify({
                'available': True,
                'loaded': False,
                'message': 'Kronos model available but not loaded'
            })
    else:
        return jsonify({
            'available': False,
            'loaded': False,
            'message': 'Kronos model library not available, please install related dependencies'
        })


@app.route('/portfolio')
def portfolio_lab():
    """Portfolio Lab page"""
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

def fetch_rag_context(symbol):
    """Fetch News, Stakeholders, and Status for RAG context"""
    try:
        conn = sqlite3.connect(DB_PATH)
        # 1. Fetch Company Info
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, sector FROM companies WHERE symbol = ?", (symbol,))
        company = cursor.fetchone()
        if not company:
            return "Company not found in nucleus."
        
        company_id, name, sector = company
        
        # 2. Fetch Latest News
        news_df = pd.read_sql_query("SELECT date, headline, content FROM news WHERE company_id = ? ORDER BY date DESC LIMIT 3", conn, params=(company_id,))
        
        # 3. Fetch Stakeholders
        owners_df = pd.read_sql_query("SELECT owner_name, share_percentage FROM stakeholders WHERE company_id = ? ORDER BY share_percentage DESC", conn, params=(company_id,))
        
        # 4. Fetch Status
        status_df = pd.read_sql_query("SELECT status, update_date, details FROM company_status WHERE company_id = ? ORDER BY update_date DESC LIMIT 1", conn, params=(company_id,))
        
        conn.close()
        
        # Construct Context String
        context = f"Company: {name} ({symbol}) | Sector: {sector}\n"
        
        if not status_df.empty:
            s = status_df.iloc[0]
            context += f"CURRENT STATUS: {s['status']} (as of {s['update_date']}). Details: {s['details']}\n"
            
        if not owners_df.empty:
            context += "MAJOR OWNERS: " + ", ".join([f"{r['owner_name']} ({r['share_percentage']}%)" for _, r in owners_df.iterrows()]) + "\n"
            
        if not news_df.empty:
            context += "LATEST NEWS:\n"
            for _, r in news_df.iterrows():
                context += f"- [{r['date']}] {r['headline']}: {r['content']}\n"
        
        return context
    except Exception as e:
        return f"Error fetching RAG context: {str(e)}"

@app.route('/api/valdis/chat', methods=['POST'])
def api_valdis_chat():
    data = request.json
    message = data.get('message', '')
    symbol = data.get('symbol', 'Unknown')
    context_ui = data.get('context', '')
    
    # RAG: Fetch Deep Context from Database
    rag_context = fetch_rag_context(symbol)
    combined_context = f"{rag_context}\n\nUI State Context: {context_ui}"
    
    # Check if a custom API key is set
    valdis_api_key = os.environ.get('VALDIS_API_KEY')
    
    if valdis_api_key:
        import requests
        try:
            # Detect if it's a Gemini API key (starts with AIza)
            if valdis_api_key.startswith("AIza"):
                # Google Gemini API Implementation with model fallback
                gemini_models = [
                    "gemini-1.5-flash",
                    "gemini-1.5-pro",
                    "gemini-pro",
                ]
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": f"SYSTEM: You are Valdis Copilot, an expert financial AI analyst. Use this context to answer: {combined_context}.\nUSER: {message}"
                        }]
                    }]
                }
                last_error = None
                for model_name in gemini_models:
                    try:
                        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={valdis_api_key}"
                        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
                        if response.status_code == 200:
                            res_json = response.json()
                            reply_text = res_json['candidates'][0]['content']['parts'][0]['text']
                            return jsonify({"success": True, "reply": reply_text})
                        elif response.status_code in (429, 503):
                            last_error = f"{model_name}: {response.status_code} - busy"
                            continue  # Try next model
                        else:
                            last_error = f"{model_name}: {response.status_code} - {response.text[:100]}"
                            break
                    except Exception as model_e:
                        last_error = str(model_e)
                        continue
                return jsonify({"success": False, "error": f"All Gemini models unavailable: {last_error}"})
            else:
                # OpenAI style fallback
                headers = {
                    "Authorization": f"Bearer {valdis_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": os.environ.get('VALDIS_MODEL', 'gpt-3.5-turbo'),
                    "messages": [
                        {"role": "system", "content": f"You are Valdis Copilot, an expert financial AI assistant. Context: {combined_context}"},
                        {"role": "user", "content": message}
                    ]
                }
                api_url = os.environ.get('VALDIS_API_URL', 'https://api.openai.com/v1/chat/completions')
                response = requests.post(api_url, headers=headers, json=payload)
                response.raise_for_status()
                reply_text = response.json()['choices'][0]['message']['content']
                return jsonify({"success": True, "reply": reply_text})
        except Exception as e:
            return jsonify({"success": False, "error": f"Valdis API communication failed: {str(e)}"})
    else:
        # Fallback simulated response if no API key is provided
        # This keeps the UI working independently
        reply_msg = f"**Valdis Simulated Response:**\nI received your query: *'{message}'*.\n\n"
        if "No market data" in combined_context:
            reply_msg += "I cannot provide a deep analysis until you load market data and run a prediction."
        else:
            reply_msg += f"Based on the context (Symbol: {symbol}) provided, the system confidence is tracking the market trends. Consider the Sharpe ratio and GARCH volatility as trailing indicators for risk management.\n\n*(Note: Set the `VALDIS_API_KEY` environment variable to connect to a real LLM like Gemini or ChatGPT).* "
            
        return jsonify({"success": True, "reply": reply_msg})


if __name__ == '__main__':
    print("Starting Valdis Web UI & Core Engine...")
    print(f"Model availability: {MODEL_AVAILABLE}")
    if MODEL_AVAILABLE:
        print("Tip: You can load Kronos model through /api/load-model endpoint")
    else:
        print("Tip: Will use simulated data for demonstration")
    
    app.run(debug=True, host='0.0.0.0', port=7070)
