import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_explanation(ticker: str, forecast: list):
    avg_prediction = sum([point['yhat'] for point in forecast]) / len(forecast)
    prompt = f"""
    Given that the predicted average price of {ticker} over the next {len(forecast)} days is approximately {avg_prediction:.2f}, explain this to a beginner investor in simple, friendly terms. Mention market trends if possible.
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()
