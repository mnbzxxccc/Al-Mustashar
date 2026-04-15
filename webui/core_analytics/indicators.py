import pandas as pd
import numpy as np

def calculate_bollinger_bands(series: pd.Series, window=20, num_std=2):
    """Calculate Bollinger Bands"""
    rolling_mean = series.rolling(window=window).mean()
    rolling_std = series.rolling(window=window).std()
    upper_band = rolling_mean + (rolling_std * num_std)
    lower_band = rolling_mean - (rolling_std * num_std)
    return upper_band, rolling_mean, lower_band

def calculate_rsi(series: pd.Series, window=14):
    """Calculate Relative Strength Index (RSI)"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    
    avg_gain = gain.rolling(window=window, min_periods=1).mean()
    avg_loss = loss.rolling(window=window, min_periods=1).mean()
    
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(series: pd.Series, fast=12, slow=26, signal=9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    fast_ema = series.ewm(span=fast, adjust=False).mean()
    slow_ema = series.ewm(span=slow, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    macd_histogram = macd_line - signal_line
    return macd_line, signal_line, macd_histogram

def calculate_mfi(df: pd.DataFrame, window=14):
    """Calculate Money Flow Index (MFI)"""
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    raw_money_flow = typical_price * df['volume']
    
    # Identify positive and negative flow
    positive_flow = []
    negative_flow = []
    
    for i in range(len(typical_price)):
        if i == 0:
            positive_flow.append(0)
            negative_flow.append(0)
            continue
            
        if typical_price.iloc[i] > typical_price.iloc[i-1]:
            positive_flow.append(raw_money_flow.iloc[i])
            negative_flow.append(0)
        elif typical_price.iloc[i] < typical_price.iloc[i-1]:
            positive_flow.append(0)
            negative_flow.append(raw_money_flow.iloc[i])
        else:
            positive_flow.append(0)
            negative_flow.append(0)
            
    pos_flow_series = pd.Series(positive_flow, index=df.index)
    neg_flow_series = pd.Series(negative_flow, index=df.index)
    
    pos_flow_sum = pos_flow_series.rolling(window=window, min_periods=1).sum()
    neg_flow_sum = neg_flow_series.rolling(window=window, min_periods=1).sum()
    
    money_flow_ratio = pos_flow_sum / (neg_flow_sum + 1e-10)
    mfi = 100 - (100 / (1 + money_flow_ratio))
    return mfi

def calculate_sharpe_ratio(series: pd.Series, risk_free_rate=0.0):
    """Calculate annualized Sharpe Ratio from daily prices"""
    returns = series.pct_change().dropna()
    if len(returns) < 2 or returns.std() == 0:
        return 0.0
    
    # Assuming 252 trading days roughly
    excess_returns = returns - (risk_free_rate / 252)
    sharpe = np.sqrt(252) * (excess_returns.mean() / excess_returns.std())
    return sharpe

def calculate_confidence_score(pred_dict: dict, current_price: float):
    """
    Calculate a synthetic AI confidence score.
    High standard deviation between Best/Worst bounds = low confidence.
    Tight bounds = high confidence.
    """
    if isinstance(pred_dict, dict) and "best" in pred_dict and "worst" in pred_dict:
        avg_price = pred_dict["avg"]["close"].values[-1]
        best_price = pred_dict["best"]["close"].values[-1]
        worst_price = pred_dict["worst"]["close"].values[-1]
        
        spread_pct = (best_price - worst_price) / current_price
        
        # Base confidence 90%, reduces as spread increases. 
        # If spread is 10% of price -> confidence = 85%. Spread = 50% -> confidence = 65%.
        confidence = 100 - (spread_pct * 50)
        confidence = min(max(confidence, 40), 99) # limit between 40% and 99%
        return float(round(confidence, 1))
    
    return 75.0 # default single path confidence

def generate_sentiment_analysis(current_mfi: float, current_macd_hist: float):
    """
    Generate an artificial (or data-driven) market sentiment signal.
    """
    sentiment_score = 50
    if current_mfi > 60:
        sentiment_score += 20
    elif current_mfi < 40:
        sentiment_score -= 20
        
    if current_macd_hist > 0:
        sentiment_score += 15
    else:
        sentiment_score -= 15
        
    if sentiment_score > 65:
        return {"status": "Bullish", "icon": "🟢", "desc": "Positive institutional money flow detected."}
    elif sentiment_score < 35:
        return {"status": "Bearish", "icon": "🔴", "desc": "Negative liquidity drain, potential sell-off."}
    else:
        return {"status": "Neutral", "icon": "⚪", "desc": "Market sentiment is currently balanced."}
