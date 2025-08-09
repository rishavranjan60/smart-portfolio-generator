from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

# Safe import of modules
try:
    from model.forecast import forecast_stock
except ImportError:
    def forecast_stock(ticker: str, days: int):
        return []

try:
    from genai.explainer import generate_explanation
except ImportError:
    def generate_explanation(ticker: str, forecast: list, days: int):
        return "Explanation not available (module not deployed on Lambda)."

# Request schema using Pydantic
class PredictRequest(BaseModel):
    ticker: str
    days: int

# FastAPI app instance
app = FastAPI()

# CORS setup for local and production frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://smart-portfolio-generator-iota.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prediction route with explanation
@app.post("/predict")
async def predict(data: PredictRequest):
    forecast = forecast_stock(data.ticker, data.days)
    explanation = generate_explanation(data.ticker, forecast, data.days)
    return {
        "ticker": data.ticker.upper(),
        "forecast": forecast,
        "explanation": explanation,
    }

# Root health check
@app.get("/")
def read_root():
    return {"message": "Smart Portfolio Generator API is running "}

# AWS Lambda handler entry point
handler = Mangum(app)
