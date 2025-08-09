import os
import yfinance as yf
import pandas as pd
import numpy as np

try:
    from prophet import Prophet  # optional, for local use only
    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False


def _prophet_forecast(df: pd.DataFrame, days: int):
    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(periods=days)
    forecast = model.predict(future)
    out = forecast[["ds", "yhat"]].tail(days)
    out["ds"] = out["ds"].dt.strftime("%Y-%m-%dT00:00:00")
    return out.to_dict(orient="records")


def _linear_regression_forecast(close: pd.Series, days: int):
    close = close.astype(float).dropna()
    if len(close) < 10:
        return []
    x = np.arange(len(close))
    y = close.values
    m, b = np.polyfit(x, y, 1)

    future_x = np.arange(len(close), len(close) + days)
    preds = m * future_x + b

    last_date = close.index[-1]
    future_dates = pd.bdate_range(start=last_date + pd.Timedelta(days=1), periods=days)

    return [
        {"ds": d.strftime("%Y-%m-%dT00:00:00"), "yhat": float(round(p, 4))}
        for d, p in zip(future_dates, preds)
    ]


def forecast_stock(ticker: str, days: int = 30):
    df = yf.download(ticker, period="2y", interval="1d")
    if df.empty:
        return []

    df = df.dropna()
    df_p = df.reset_index()[["Date", "Close"]].rename(columns={"Date": "ds", "Close": "y"})
    df_p["ds"] = pd.to_datetime(df_p["ds"])

    disable_prophet = os.getenv("DISABLE_PROPHET", "").lower() in {"1", "true", "yes"}
    use_prophet = HAS_PROPHET and not disable_prophet

    try:
        if use_prophet:
            return _prophet_forecast(df_p, days)
        return _linear_regression_forecast(df["Close"], days)
    except Exception:
        return _linear_regression_forecast(df["Close"], days)
