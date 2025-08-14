# main.py
import os
import logging
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mangum import Mangum

from model.forecast import forecast_stock
from genai.explainer import generate_explanation
from model.recommend import recommend_portfolio

logger = logging.getLogger("uvicorn")

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

class PredictRequest(BaseModel):
    ticker: str
    days: int

class RecommendRequest(BaseModel):
    budget_eur: float
    months: int = 6
    top_n: int = 10

app = FastAPI()

# Allowed origins setup
default_origins = [
    "http://localhost:5173",
    "https://smart-portfolio-generator-iota.vercel.app",
]
env_origins = os.getenv("ALLOWED_ORIGINS", ",".join(default_origins))
allow_origins = [o.strip().rstrip("/") for o in env_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    max_age=86400,
)

# Universe tickers file path
UNIVERSE_FILE = os.path.join(os.path.dirname(__file__), "data", "tickers.txt")

@app.get("/")
def read_root():
    return {"message": "Smart Portfolio Generator API is running 🚀"}

@app.post("/predict")
async def predict(data: PredictRequest):
    """Generate forecast for a ticker."""
    try:
        forecast = forecast_stock(data.ticker, data.days)
        explanation = generate_explanation(data.ticker, forecast, data.days)
        return {"ticker": data.ticker.upper(), "forecast": forecast, "explanation": explanation}
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Prediction failed")

@app.post("/recommend")
def recommend(req: RecommendRequest):
    """Generate a portfolio recommendation."""
    try:
        return recommend_portfolio(
            budget_eur=req.budget_eur,
            months=req.months,
            top_n=req.top_n,
            universe_file=UNIVERSE_FILE,
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Failed to compute recommendations")

# ---------- TEMP DIAGNOSTICS ----------
@app.get("/__diag")
def diag(limit: int = 5):
    """Show diagnostic info about the ticker universe."""
    try:
        from model import recommend as recmod
        from model.recommend import _load_universe
        path = os.path.join(os.path.dirname(__file__), "data", "tickers.txt")
        uni_full = _load_universe(path)
        uni = uni_full[:max(1, int(limit))]
        return {
            "version": getattr(recmod, "VERSION", "unknown"),
            "universe_file": path,
            "universe_exists": os.path.exists(path),
            "universe_count": len(uni_full),
            "used_tickers": uni,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ✅ Finnhub connectivity check with FX conversion
@app.get("/__finncheck")
def finnhub_check(symbol: str = "SAP"):
    """
    Check Finnhub quote endpoint and return current price in EUR.
    If US stock, converts USD → EUR using Finnhub forex rates.
    """
    try:
        # Get last price in native currency
        quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        r = requests.get(quote_url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if "c" not in data or not data["c"]:
            return {"ok": False, "reason": "no price"}

        price = float(data["c"])

        # Convert USD → EUR if it's a US-listed stock
        if "." not in symbol:  # No exchange suffix → probably US
            fx_url = f"https://finnhub.io/api/v1/forex/rates?token={FINNHUB_API_KEY}"
            fx_r = requests.get(fx_url, timeout=10)
            fx_r.raise_for_status()
            rates = fx_r.json().get("quote", {})
            usd_eur = float(rates.get("USDEUR", 1.0))
            price *= usd_eur

        return {
            "ok": True,
            "symbol": symbol,
            "current_price_eur": round(price, 2)
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

# AWS Lambda entry
handler = Mangum(app)
