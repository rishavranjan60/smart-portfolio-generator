# genai/explainer.py

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Generate explanation using Gemini
def generate_explanation(ticker: str, forecast: str, duration: int = None) -> str:
    prompt = f"""
    You are a financial advisor. Based on this forecast:

    {forecast}

    Explain in a few sentences why investing in {ticker} is a good idea for the next {duration} days.
    Keep it simple, clear, and helpful.
    """

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Failed to generate explanation: {str(e)}"
