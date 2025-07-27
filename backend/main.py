from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictRequest(BaseModel):
    ticker: str
    days: int

@app.post("/api/predict")
def predict(request: PredictRequest):
    return {"message": f"Forecasting {request.ticker} for {request.days} days."}
