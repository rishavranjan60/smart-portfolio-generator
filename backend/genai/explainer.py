# genai/explainer.py
import os
import google.generativeai as genai

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("⚠️ GOOGLE_API_KEY is missing at import time. Gemini will be disabled.")
else:
    genai.configure(api_key=GOOGLE_API_KEY)

def generate_explanation(ticker: str, forecast: list, duration: int | None = None) -> str:
    """
    Generates a short explanation via Gemini. Falls back safely if:
      - no key is present,
      - forecast is empty,
      - Gemini errors.
    """
    try:
        if not GOOGLE_API_KEY:
            return "Explanation not available (GOOGLE_API_KEY not set on server)."

        if not forecast:
            return "No forecast data to explain."

        # average price (guard against missing yhat)
        try:
            vals = [float(p.get("yhat", 0)) for p in forecast if "yhat" in p]
            if not vals:
                return "No forecast data to explain."
            avg_prediction = sum(vals) / len(vals)
        except Exception:
            return "No forecast data to explain."

        # keep the prompt lean so it’s fast/cheap
        prompt = (
            f"Explain in 3 short sentences the next {duration or len(forecast)} days outlook for {ticker}.\n"
            f"Average forecasted price: ${avg_prediction:.2f}.\n"
            f"Keep it beginner-friendly and avoid guarantees."
        )

        # Use a fast text-only model
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content(prompt)

        text = (getattr(resp, "text", "") or "").strip()
        return text or "No explanation returned by Gemini."

    except Exception as e:
        print(f"❌ Gemini explanation failed: {e}")
        return f"Explanation not available (Gemini error)."
