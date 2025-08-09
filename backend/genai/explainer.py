# genai/explainer.py

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini with API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError(" GOOGLE_API_KEY not set in .env file.")

genai.configure(api_key=GOOGLE_API_KEY)

# Generate explanation using Gemini
def generate_explanation(ticker: str, forecast: list, duration: int = None) -> str:
    try:
        # Calculate average forecasted price
        avg_prediction = sum([point['yhat'] for point in forecast]) / len(forecast)

        # Prepare Gemini prompt
        prompt = f"""
        You are a helpful financial advisor.

        The forecasted average price of {ticker.upper()} over the next {duration or len(forecast)} days is approximately ${avg_prediction:.2f}.

        Explain this to a beginner investor in simple, friendly terms. Highlight trends or possible market behavior if relevant.
        """

        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)

        return response.text.strip() if hasattr(response, "text") else "Explanation not available."

    except Exception as e:
        return f"Failed to generate explanation: {str(e)}"
