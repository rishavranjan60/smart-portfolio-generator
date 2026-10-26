# Smart Portfolio Generator

A portfolio and stock-forecasting application with a React + TypeScript frontend and a FastAPI backend. The API exposes `/predict` and `/recommend` endpoints and includes a Mangum entry point for AWS Lambda.

## Project layout

- `frontend/`: Vite UI with Chart.js visualizations.
- `backend/main.py`: FastAPI routes and CORS configuration.
- `backend/model/`: forecasting and portfolio recommendation logic.
- `backend/genai/`: generated explanations.
- `backend/data/tickers.txt`: ticker universe.
- `backend/requirements.txt`: Python dependencies.
- `backend/serverless.yml`: deployment configuration.

## Frontend development

With Node.js and npm installed:

```bash
cd frontend
npm ci
npm run dev
```

Run `npm run lint` and `npm run build` in the same directory to check the frontend.

## Backend entry point

Use an isolated Python environment and install dependencies from `backend/requirements.txt`. From `backend/`, the local API entry point is:

```bash
python -m uvicorn main:app --reload
```

API documentation is available at http://localhost:8000/docs once startup succeeds. Review provider configuration in `backend/genai/` and `backend/model/` before using prediction or recommendation endpoints. `backend/main.py` reads `FINNHUB_API_KEY` and accepts comma-separated `ALLOWED_ORIGINS`; configure required provider credentials in the backend environment and keep them out of Git.

The default CORS origins include http://localhost:5173. Ensure the frontend API URL points to the backend you intend to use.

## Scope

Forecasts and generated explanations are experimental outputs, not guaranteed investment outcomes. Local dependency installation and provider connectivity need to be verified for your environment.
