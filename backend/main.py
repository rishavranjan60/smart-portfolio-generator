# main.py
import os
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

# Safe imports (fallbacks if optional deps missing on Lambda)
try:
    from model.forecast import forecast_stock
    from genai.explainer import generate_explanation
except ImportError:
    forecast_stock = lambda ticker, days: []
    generate_explanation = lambda ticker, forecast, days: "Explanation not available (module not deployed on Lambda)."

class PredictRequest(BaseModel):
    ticker: str
    days: int

app = FastAPI()

# ── CORS: read from env, fallback to localhost + your Vercel app ─────────────────
default_origins = [
    "http://localhost:5173",
    "https://smart-portfolio-generator-iota.vercel.app",
]
env_origins = os.getenv("ALLOWED_ORIGINS", ",".join(default_origins))
allow_origins = [o.strip().rstrip("/") for o in env_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,         # explicit domains
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    max_age=86400,  # cache preflight 1 day
)

@app.post("/predict")
async def predict(data: PredictRequest):
    forecast = forecast_stock(data.ticker, data.days)
    explanation = generate_explanation(data.ticker, forecast, data.days)
    return {
        "ticker": data.ticker.upper(),
        "forecast": forecast,
        "explanation": explanation,
    }

@app.get("/")
def read_root():
    return {"message": "Smart Portfolio Generator API is running 🚀"}

handler = Mangum(app)
