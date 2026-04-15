import sqlite3
import pandas as pd
import numpy as np
from pypfopt import risk_models, expected_returns, EfficientFrontier, plotting
import matplotlib.pyplot as plt
import io
import base64
from .risk_engine import simulate_currency_impact

DATABASE_PATH = r"E:\Kronos-master\isx_data_hub\isx_nucleus_enhanced.db"

def get_multi_symbol_prices(symbols, lookback=500):
    """
    Fetch historical close prices for a list of symbols and pivot them for portfolio analysis.
    """
    if not symbols:
        return pd.DataFrame()
        
    conn = sqlite3.connect(DATABASE_PATH)
    
    # Construct query for multiple symbols
    placeholders = ', '.join(['?'] * len(symbols))
    query = f"""
    SELECT c.symbol, p.date, p.close
    FROM prices p
    JOIN companies c ON p.company_id = c.id
    WHERE c.symbol IN ({placeholders})
    ORDER BY p.date ASC
    """
    
    df = pd.read_sql_query(query, conn, params=symbols)
    conn.close()
    
    if df.empty:
        return pd.DataFrame()
        
    # Pivot to have symbols as columns
    pivot_df = df.pivot(index='date', columns='symbol', values='close')
    
    # Fill missing values (important for ISX where some days have no trades)
    pivot_df = pivot_df.ffill().dropna()
    
    return pivot_df[-lookback:]

def optimize_portfolio(symbols, risk_aversion=1.0, currency_change=0.0):
    """
    Optimize portfolio weights using Mean-Variance Optimization.
    :param currency_change: Manual USD/IQD change scenario (%)
    """
    df = get_multi_symbol_prices(symbols)
    if df.empty or len(df.columns) < 2:
        return {"error": "Insufficient data for portfolio optimization (need at least 2 symbols with concurrent data)."}

    try:
        # 1. Calculate expected returns and sample covariance
        mu = expected_returns.mean_historical_return(df)
        S = risk_models.sample_cov(df)
        
        # 1.1 Apply Currency Hedge Simulation to expected returns
        # Correlation assumption: 0.6 (Bank sector etc. usually rise when USD rises in Iraq context)
        if currency_change != 0:
            mu = mu * (1 + (currency_change / 100 * 0.6))

        # 2. Optimize for maximal Sharpe ratio
        ef = EfficientFrontier(mu, S)
        # We can optimize for max_sharpe or min_volatility
        # Let's use max_sharpe as default
        weights = ef.max_sharpe()
        cleaned_weights = ef.clean_weights()
        
        # 3. Performance metrics
        perf = ef.portfolio_performance(verbose=False)
        # perf is (expected return, volatility, Sharpe ratio)
        
        return {
            "weights": dict(cleaned_weights),
            "expected_annual_return": round(perf[0] * 100, 2),
            "annual_volatility": round(perf[1] * 100, 2),
            "sharpe_ratio": round(perf[2], 2)
        }
    except Exception as e:
        return {"error": str(e)}

def get_correlation_matrix(symbols):
    """
    Return the correlation matrix for a set of symbols.
    """
    df = get_multi_symbol_prices(symbols)
    if df.empty:
        return {}
        
    corr = df.pct_change().corr()
    return corr.to_dict()
