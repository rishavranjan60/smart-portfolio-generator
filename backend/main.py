from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from model.forecast import forecast_stock  # ✅ Forecast function
from genai.explainer import generate_explanation  # ✅ Gemini explanation function

# 📘 Request body schema
class PredictRequest(BaseModel):
    ticker: str
    days: int

# 🚀 Initialize FastAPI app
app = FastAPI()

# 🌐 Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://smart-portfolio-generator-iota.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔮 Prediction + Gemini Explanation Endpoint
@app.post("/predict")
async def predict(data: PredictRequest):
    forecast = forecast_stock(data.ticker, data.days)
    explanation = generate_explanation(data.ticker, forecast, data.days)  # ✅ Now passes duration too

    return {
        "ticker": data.ticker.upper(),
        "forecast": forecast,
        "explanation": explanation,
    }

# 🏠 Health check
@app.get("/")
def read_root():
    return {"message": "Smart Portfolio Generator API is running 🚀"}

# ✅ For AWS Lambda deployments
handler = Mangum(app)
