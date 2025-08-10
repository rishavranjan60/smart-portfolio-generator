# model/forecast.py
import yfinance as yf
import pandas as pd
from datetime import timedelta

# Try to use numpy for a tiny linear trend; fall back to flat if missing
try:
    import numpy as np
except Exception:
    np = None

def _linear_trend(values: pd.Series) -> float:
    """Return simple slope of the last N closes."""
    if np is None or len(values) < 2:
        return 0.0
    y = values.to_numpy(dtype=float)
    x = np.arange(len(y), dtype=float)
    # slope only
    slope = np.polyfit(x, y, 1)[0]
    return float(slope)

def forecast_stock(ticker: str, days: int = 30):
    # Download last 2y of daily closes
    df = yf.download(ticker, period="2y", interval="1d", progress=False)
    if df.empty or "Close" not in df.columns:
        return []

    df = df.reset_index()[["Date", "Close"]].rename(columns={"Date": "ds", "Close": "y"})
    df = df.dropna()

    if df.empty:
        return []

    # Use last 20 trading days to estimate a simple linear trend
    lookback = min(20, len(df))
    recent = df["y"].tail(lookback)
    slope = _linear_trend(recent)

    last_date = pd.to_datetime(df["ds"].iloc[-1])
    last_price = float(df["y"].iloc[-1])

    # Generate naive forecast: last price + slope * step
    out = []
    for i in range(1, days + 1):
        yhat = last_price + slope * i
        ds = (last_date + timedelta(days=i)).strftime("%Y-%m-%d")
        out.append({"ds": ds, "yhat": float(yhat)})

    return out
