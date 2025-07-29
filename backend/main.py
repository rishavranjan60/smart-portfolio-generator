from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from model.forecast import forecast_stock  # ✅ Forecast function
from genai.explainer import generate_explanation  # ✅ Explanation function

# 📘 Request body schema
class PredictRequest(BaseModel):
    ticker: str
    days: int

# 🚀 Initialize FastAPI app
app = FastAPI()

# 🌐 Enable CORS for frontend (adjust origin as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://smart-portfolio-generator-iota.vercel.app"],  # Update with frontend URL if deployed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔮 Prediction + Explanation API endpoint
@app.post("/predict")
async def predict(data: PredictRequest):
    forecast = forecast_stock(data.ticker, data.days)
    explanation = generate_explanation(data.ticker, forecast)

    return {
        "ticker": data.ticker,
        "forecast": forecast,
        "explanation": explanation,
    }

# 🏠 Root API health check
@app.get("/")
def read_root():
    return {"message": "Smart Portfolio Generator API is running 🚀"}

# ✅ AWS Lambda compatibility
handler = Mangum(app)
