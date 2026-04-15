import numpy as np
import pandas as pd
from arch import arch_model

def calculate_garch_volatility(returns: pd.Series, horizon=30):
    """
    Predict future volatility using a GARCH(1,1) model.
    :param returns: Daily returns of the asset
    :param horizon: Forecast horizon in days
    :return: Forecasted annualized volatility
    """
    if len(returns) < 50:
        return None
    
    # Scale returns for better convergence
    scaled_returns = returns * 100
    
    try:
        model = arch_model(scaled_returns, vol='Garch', p=1, q=1, dist='normal', rescale=False)
        res = model.fit(disp='off')
        
        # Forecast
        forecasts = res.forecast(horizon=horizon)
        # GARCH forecasts variance (sigma^2). We need sqrt of mean variance.
        forecasted_variance = forecasts.variance.values[-1, :]
        forecasted_vol = np.sqrt(np.mean(forecasted_variance)) / 100 # scale back
        
        # Annualize
        annualized_vol = forecasted_vol * np.sqrt(252)
        return float(annualized_vol)
    except:
        return None

def calculate_sortino_ratio(series: pd.Series, target_return=0.0):
    """
    Calculate the Sortino Ratio (Reward to Downside Volatility).
    """
    returns = series.pct_change().dropna()
    if len(returns) < 10:
        return 0.0
    
    avg_return = returns.mean()
    downside_returns = returns[returns < target_return]
    
    if len(downside_returns) < 2:
        return 0.0
        
    downside_std = downside_returns.std()
    
    if downside_std == 0:
        return 0.0
        
    sortino = (avg_return - target_return) / downside_std
    # Annualize
    return float(sortino * np.sqrt(252))

def detect_liquidity_gaps(df: pd.DataFrame, volume_threshold_pct=5):
    """
    Identify periods of low liquidity or significant gaps in price without volume.
    """
    if 'volume' not in df.columns or len(df) < 10:
        return []
    
    median_volume = df['volume'].median()
    gaps = []
    
    for i in range(1, len(df)):
        vol = df['volume'].iloc[i]
        price_change = abs(df['close'].iloc[i] - df['close'].iloc[i-1]) / df['close'].iloc[i-1]
        
        # Condition: High price jump with very low relative volume
        if vol < (median_volume * (volume_threshold_pct / 100)) and price_change > 0.03:
            gaps.append({
                'date': df['date'].iloc[i] if 'date' in df.columns else str(df.index[i]),
                'price_change_pct': round(price_change * 100, 2),
                'volume_ratio': round(vol / median_volume, 4),
                'risk_level': 'High (Low Liquidity Gap)'
            })
            
    return gaps

def simulate_currency_impact(original_prices: np.array, usd_iqd_change_pct: float, correlation=0.6):
    """
    Simulate how a change in USD/IQD parallel market might affect asset value.
    This is useful for 'Currency Hedge' scenarios.
    
    :param original_prices: The predicted price path (Average scenario)
    :param usd_iqd_change_pct: User selected change (e.g. 5.0 for 5% USD appreciation)
    :param correlation: Assumption of how closely the asset follows USD jumps (positive means asset rises with USD)
    :return: Adjusted price path
    """
    # Simply adjust the path based on correlation and currency move
    adjustment = 1 + (usd_iqd_change_pct / 100 * correlation)
    return original_prices * adjustment
