import pandas as pd
import numpy as np

def generate_financial_rationale(x_df: pd.DataFrame, avg_df: pd.DataFrame) -> str:
    """
    Generates a financial rationale based on the historical context (x_df)
    and the forecasted expected scenario (avg_df).
    
    :param x_df: The recent historical data before the prediction point.
    :param avg_df: The predicted 'average/expected' scenario by the Kronos model.
    :return: A string detailing the financial logic.
    """
    if len(x_df) < 20:
        return "Not enough historical data to generate a robust financial technical logic report."
        
    hist_close = x_df['close'].values
    pred_close = avg_df['close'].values
    
    # 1. Historical Momentum (RSI estimate on last 14 days)
    delta = np.diff(hist_close[-15:])
    gains = np.maximum(delta, 0)
    losses = -np.minimum(delta, 0)
    avg_gain = np.mean(gains)
    avg_loss = np.mean(losses)
    
    if avg_loss == 0:
        rsi = 100
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
    # 2. Moving Averages
    ma10 = np.mean(hist_close[-10:])
    ma50 = np.mean(hist_close[-50:]) if len(hist_close) >= 50 else np.mean(hist_close)
    
    current_price = hist_close[-1]
    expected_price = pred_close[-1]
    price_delta_pct = ((expected_price - current_price) / current_price) * 100
    
    trend_hist = "Bullish" if current_price > ma50 else "Bearish"
    momentum = "Overbought" if rsi > 70 else ("Oversold" if rsi < 30 else "Neutral")
    
    # 3. Model Forecast Verdict
    forecast_dir = "الصعود" if expected_price > current_price else "الهبوط"
    
    rationale = f"💡 **التحليل المالي التقني (Financial Rationale):**\n"
    rationale += f"بناءً على معطيات السهم الحقيقية، السعر الحالي يقع عند ({current_price:.2f}). "
    
    if trend_hist == "Bullish":
        rationale += f"السهم تاريخياً يعتبر في مسار إيجابي لأنه يتداول أعلى من متوسطه المتحرك في الـ 50 يوماً ({ma50:.2f}). "
    else:
        rationale += f"السهم تاريخياً يعاني من ضغط بيعي حيث يتداول أسفل متوسطه في الـ 50 يوماً ({ma50:.2f}). "
        
    rationale += f"مؤشر الزخم (RSI) يقف عند مستويات ({rsi:.1f}) وهو ما يدل على حالة ({momentum}). "
    
    rationale += f"\n\n🤖 **استنتاج نموذج Kronos:**\n"
    rationale += f"الموديل الذكي التقط هذه المؤشرات مع حجم السيولة (Volume) وتوقع سيناريو مستقبلي يميل إلى **{forecast_dir}** بنسبة {abs(price_delta_pct):.2f}% خلال فترة التنبؤ القادمة، ليستقر عند حوالي ({expected_price:.2f}) كسيناريو متوسط."

    return rationale
