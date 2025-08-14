# backend/model/forecast.py
from __future__ import annotations

import os, time, math
from datetime import datetime, timedelta, timezone
import requests
import pandas as pd

try:
    import numpy as np
except Exception:
    np = None

FINNHUB_TOKEN = os.getenv("FINNHUB_API_KEY", "")
BASE = "https://finnhub.io/api/v1"  # docs: /stock/candle, /quote, /forex/rates

def _linear_trend(values: pd.Series) -> float:
    if np is None or len(values) < 2:
        return 0.0
    x = np.arange(len(values), dtype=float)
    y = values.to_numpy(dtype=float)
    return float(np.polyfit(x, y, 1)[0])

def _synthetic_forecast(base_price: float, days: int, slope: float = 0.5):
    out = []
    today = pd.Timestamp.utcnow().normalize()
    for i in range(1, days + 1):
        ds = (today + timedelta(days=i)).strftime("%Y-%m-%d")
        out.append({"ds": ds, "yhat": float(base_price + slope * i)})
    return out

def _fh_get(path: str, params: dict) -> dict:
    if not FINNHUB_TOKEN:
        return {}
    p = dict(params or {})
    p["token"] = FINNHUB_TOKEN
    r = requests.get(f"{BASE}{path}", params=p, timeout=10)
    if r.status_code != 200:
        return {}
    return r.json() or {}

def _fh_stock_candles(symbol: str, from_ts: int, to_ts: int, res: str = "D") -> pd.Series:
    js = _fh_get("/stock/candle", {"symbol": symbol, "resolution": res, "from": from_ts, "to": to_ts})
    if not js or js.get("s") != "ok":
        return pd.Series(dtype=float)
    closes = js.get("c") or []
    stamps = js.get("t") or []
    if not closes or not stamps or len(closes) != len(stamps):
        return pd.Series(dtype=float)
    idx = pd.to_datetime(pd.Series(stamps), unit="s", utc=True).tz_convert(None)
    s = pd.Series(closes, index=idx, name="Close").astype(float)
    return s.dropna()

def _fh_quote(symbol: str) -> float | None:
    js = _fh_get("/quote", {"symbol": symbol})
    c = js.get("c") if isinstance(js, dict) else None
    try:
        return float(c) if c is not None and math.isfinite(float(c)) else None
    except Exception:
        return None

def _fh_fx_rate(from_cur: str, to_cur: str) -> float:
    """Get real-time FX rate from Finnhub (e.g., USD→EUR)."""
    js = _fh_get("/forex/rates", {})
    if not js or "quote" not in js:
        return 1.0
    rates = js["quote"]
    key = f"{from_cur}{to_cur}"
    return float(rates.get(key, 1.0))

def forecast_stock(ticker: str, days: int = 30):
    """
    Build a simple linear projection from ~2 years of daily closes (Finnhub).
    Converts USD stocks to EUR automatically using live FX.
    """
    try:
        now = datetime.now(timezone.utc)
        to_ts = int(now.timestamp())
        from_ts = int((now - timedelta(days=730)).timestamp())

        # Try candles
        s = _fh_stock_candles(ticker, from_ts, to_ts, res="D")
        if s.empty:
            base = _fh_quote(ticker) or 100.0
            slope = 0.3
        else:
            s = s.sort_index()
            base = float(s.iloc[-1])
            lookback = min(20, len(s))
            slope = _linear_trend(s.tail(lookback))

        # Detect USD stocks (no .XETR/.PAR/.SWX suffix means likely US)
        if "." not in ticker:  # crude check — US stocks
            fx_rate = _fh_fx_rate("USD", "EUR")
            base *= fx_rate
            slope *= fx_rate
        else:
            fx_rate = 1.0

        # Build forecast
        out = []
        last_date = datetime.now() if s.empty else s.index[-1]
        for i in range(1, days + 1):
            ds = (last_date + timedelta(days=i)).strftime("%Y-%m-%d")
            yhat = base + slope * i
            out.append({"ds": ds, "yhat": float(yhat)})

        return out
    except Exception as e:
        print("forecast_stock error:", e)
        return _synthetic_forecast(100.0, days, slope=0.3)
