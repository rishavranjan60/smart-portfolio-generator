import os
import requests
import pandas as pd
import numpy as np

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# --- API helpers ---
def get_price_finnhub(symbol):
    """Get latest price for a symbol from Finnhub."""
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    resp = requests.get(url).json()
    return resp.get("c")  # 'c' = current price

def get_usd_to_eur_rate():
    """Fetch current USD→EUR FX rate from Finnhub."""
    url = f"https://finnhub.io/api/v1/forex/rates?token={FINNHUB_API_KEY}"
    resp = requests.get(url).json()
    return resp.get("quote", {}).get("EUR")  # how many EUR 1 USD buys

def get_usd_per_eur_rate():
    """Convert USD→EUR to USD per EUR (for frontend display)."""
    eur_per_usd = get_usd_to_eur_rate()
    return round(1 / eur_per_usd, 4) if eur_per_usd else None

def get_price_in_eur(symbol, market="EUR"):
    """
    Fetch stock price in EUR:
      - If market == 'USD', convert using live FX
      - If market == 'EUR', return as-is
    """
    price = get_price_finnhub(symbol)
    if not price:
        return None
    if market.upper() == "USD":
        rate_usd_to_eur = get_usd_to_eur_rate()
        if rate_usd_to_eur:
            return round(price * rate_usd_to_eur, 2)
    return round(price, 2)

# --- Portfolio recommendation ---
def recommend_portfolio(budget_eur, months, top_n, universe_file):
    # Load tickers + market mapping (example: "AAPL,USD" or "SAP,EUR")
    tickers = []
    markets = {}
    with open(universe_file) as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) == 2:
                ticker, market = parts
            else:
                ticker, market = parts[0], "USD"  # default to USD
            tickers.append(ticker)
            markets[ticker] = market

    # Get prices in EUR
    prices_eur = {}
    for t in tickers:
        prices_eur[t] = get_price_in_eur(t, markets[t])

    df = pd.DataFrame({"ticker": tickers, "last": [prices_eur[t] for t in tickers]})
    df.dropna(inplace=True)

    # Example simple sort: lowest price first
    df = df.sort_values("last").head(top_n)

    # Simple equal-weight allocation
    df["weight"] = 1 / len(df)
    df["alloc"] = budget_eur * df["weight"]
    df["shares"] = (df["alloc"] / df["last"]).round(4)
    df["cost"] = df["shares"] * df["last"]

    # Placeholder values for frontend-required metrics
    df["momentum6m"] = np.nan
    df["sharpe"] = np.nan
    df["drawdown"] = np.nan

    leftover = budget_eur - df["cost"].sum()

    return {
        "currency": "EUR",
        "fx_rate_usd_per_eur": get_usd_per_eur_rate(),
        "budget_eur": budget_eur,
        "leftover_eur": round(leftover, 2),
        "horizon_months": months,
        "recommendations": df.to_dict(orient="records"),
        "chart": {"dates": [], "series": {}}  # no chart logic yet
    }
