import yfinance as yf
from prophet import Prophet
import pandas as pd

def forecast_stock(ticker, days=30):
    df = yf.download(ticker, period='2y')
    df = df.reset_index()[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})
    
    model = Prophet()
    model.fit(df)

    future = model.make_future_dataframe(periods=days)
    forecast = model.predict(future)

    return forecast[['ds', 'yhat']].tail(days).to_dict(orient="records")
