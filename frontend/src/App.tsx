import { useState } from 'react';

import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LineElement,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  LineElement,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend
);

// ---- env base URL (no trailing slash) ----------------------------------------
const RAW_BASE = (import.meta.env.VITE_API_URL || '') as string;
if (!RAW_BASE) {
  console.error('VITE_API_URL is missing. Set it in your frontend .env or Vercel env.');
}
const API_BASE_URL = RAW_BASE.replace(/\/+$/, '');

// ---- helpers -----------------------------------------------------------------
const fmtEur = (v: number | undefined | null) =>
  typeof v === 'number' && Number.isFinite(v) ? `€${v.toFixed(2)}` : '–';
const fmtPct = (v: number | undefined | null) =>
  typeof v === 'number' && Number.isFinite(v) ? `${(v * 100).toFixed(1)}%` : '–';

type ForecastPoint = { ds: string; yhat: number };

type ChartPayload = {
  dates: string[];
  series: Record<string, number[]>; // normalized values (1.0 = 100)
};

// ==== EUR recommendation rows coming from backend =============================
type Recommendation = {
  ticker: string;
  last: number;        // EUR
  momentum6m: number;  // 0..1
  sharpe: number;
  drawdown: number;    // negative fraction
  weight: number;      // 0..1
  alloc: number;       // EUR
  shares: number;      // fractional or integer
  cost: number;        // EUR
};

type RecResponse = {
  currency: 'EUR';
  fx_rate_usd_per_eur?: number;
  budget_eur: number;
  leftover_eur: number;
  horizon_months: number;
  recommendations: Recommendation[];
  chart: ChartPayload;
};

function App() {
  // ---------- Single-ticker prediction ----------------------------------------
  const [ticker, setTicker] = useState('');
  const [days, setDays] = useState(5);
  const [forecast, setForecast] = useState<ForecastPoint[]>([]);
  const [explanation, setExplanation] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchPrediction = async () => {
    setLoading(true);
    setForecast([]);
    setExplanation('');

    if (!ticker.trim()) {
      setExplanation('Please enter a valid stock ticker symbol.');
      setLoading(false);
      return;
    }
    if (!days || days <= 0) {
      setExplanation('Please enter a valid number of days.');
      setLoading(false);
      return;
    }

    const payload = { ticker: ticker.trim().toUpperCase(), days: Number(days) };
    try {
      const response = await fetch(`${API_BASE_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error(`Server error: ${response.status}`);
      const data = await response.json();
      setForecast(data.forecast || []);
      setExplanation(data.explanation || 'No explanation provided.');
    } catch (error) {
      console.error('API Error (/predict):', error);
      setExplanation('An error occurred while fetching prediction.');
    } finally {
      setLoading(false);
    }
  };

  // ---------- Portfolio recommendation (EUR) ----------------------------------
  const [amount, setAmount] = useState<number>(200); // € budget
  const [months, setMonths] = useState<number>(6);   // horizon
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [recMeta, setRecMeta] = useState<Pick<RecResponse,
    'budget_eur' | 'leftover_eur' | 'fx_rate_usd_per_eur' | 'horizon_months'
  > | null>(null);
  const [chartData, setChartData] = useState<ChartPayload | null>(null);

  const fetchRecommendations = async () => {
    setLoading(true);
    setRecs([]);
    setChartData(null);
    setRecMeta(null);

    try {
      const res = await fetch(`${API_BASE_URL}/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ budget_eur: amount, months, top_n: 10 }),
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data: RecResponse = await res.json();

      setRecs(data.recommendations || []);
      setChartData(data.chart || null);
      setRecMeta({
        budget_eur: data.budget_eur,
        leftover_eur: data.leftover_eur,
        fx_rate_usd_per_eur: data.fx_rate_usd_per_eur,
        horizon_months: data.horizon_months,
      });
    } catch (e) {
      console.error('API Error (/recommend):', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center p-6">
      <h1 className="text-3xl font-bold mb-6">📈 Smart Portfolio Predictor</h1>

      {/* -------- Portfolio Finder (Best 10) -------- */}
      <div className="w-full max-w-5xl">
        <div className="flex flex-col md:flex-row items-center gap-4 mb-4">
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(Number(e.target.value))}
            placeholder="Amount (€)"
            className="p-3 border border-gray-300 rounded-md w-44 shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            min={1}
          />
          <input
            type="number"
            value={months}
            onChange={(e) => setMonths(Number(e.target.value))}
            placeholder="Months (e.g., 6)"
            className="p-3 border border-gray-300 rounded-md w-44 shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            min={1}
          />
          <button
            onClick={fetchRecommendations}
            className="px-6 py-3 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 transition disabled:opacity-50"
            disabled={loading}
          >
            {loading ? 'Finding…' : 'Find Best 10'}
          </button>
        </div>

        {recMeta && (
          <div className="text-sm text-gray-600 mb-2">
            Budget: <span className="font-medium">{fmtEur(recMeta.budget_eur)}</span>
            {' • '}
            Leftover: <span className="font-medium">{fmtEur(recMeta.leftover_eur)}</span>
            {' • '}
            Horizon: <span className="font-medium">{recMeta.horizon_months ?? months} months</span>
            {recMeta.fx_rate_usd_per_eur && (
              <>
                {' • '}
                <span className="text-gray-500">
                  FX used: 1 EUR = ${recMeta.fx_rate_usd_per_eur.toFixed(4)} USD
                </span>
              </>
            )}
          </div>
        )}

        {recs.length > 0 && (
          <>
            <div className="w-full overflow-x-auto">
              <table className="w-full table-auto border border-gray-300 shadow-sm bg-white rounded-md mb-6 text-sm">
                <thead className="bg-gray-200">
                  <tr>
                    <th className="border p-2">#</th>
                    <th className="border p-2">Ticker</th>
                    <th className="border p-2">Last (EUR)</th>
                    <th className="border p-2">6M Mom</th>
                    <th className="border p-2">Sharpe</th>
                    <th className="border p-2">Drawdown</th>
                    <th className="border p-2">Weight %</th>
                    <th className="border p-2">Alloc (EUR)</th>
                    <th className="border p-2">Shares</th>
                    <th className="border p-2">Cost (EUR)</th>
                  </tr>
                </thead>
                <tbody className="text-center">
                  {recs.map((r, i) => (
                    <tr key={r.ticker}>
                      <td className="border p-2">{i + 1}</td>
                      <td className="border p-2">{r.ticker}</td>
                      <td className="border p-2">{fmtEur(r.last)}</td>
                      <td className="border p-2">{fmtPct(r.momentum6m)}</td>
                      <td className="border p-2">{(r.sharpe ?? 0).toFixed(2)}</td>
                      <td className="border p-2">{fmtPct(r.drawdown)}</td>
                      <td className="border p-2">{fmtPct(r.weight)}</td>
                      <td className="border p-2">{fmtEur(r.alloc)}</td>
                      <td className="border p-2">{Number(r.shares ?? 0).toFixed(4)}</td>
                      <td className="border p-2">{fmtEur(r.cost)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Weights bar chart */}
            <div className="w-full bg-white p-4 rounded shadow mb-8">
              <h3 className="font-semibold mb-3">Portfolio Weights</h3>
              <Bar
                data={{
                  labels: recs.map((r) => r.ticker),
                  datasets: [
                    {
                      label: 'Weight (%)',
                      data: recs.map((r) => (r.weight ?? 0) * 100),
                    },
                  ],
                }}
                options={{ responsive: true }}
              />
            </div>

            {/* Normalized performance (start=100) */}
            {chartData && (
              <div className="w-full bg-white p-4 rounded shadow mb-12">
                <h3 className="font-semibold mb-3">Normalized Performance (start = 100)</h3>
                <Line
                  data={{
                    labels: chartData.dates,
                    datasets: Object.entries(chartData.series).map(([t, arr]) => ({
                      label: String(t),
                      data: (arr as number[]).map((v) => v * 100), // 1.0 -> 100
                      fill: false,
                      tension: 0.25,
                    })),
                  }}
                  options={{
                    responsive: true,
                    plugins: { legend: { position: 'top' } },
                    scales: {
                      y: { title: { display: true, text: 'Index' } },
                    },
                  }}
                />
              </div>
            )}
          </>
        )}
      </div>

      {/* -------- Single-ticker Predict (original feature) -------- */}
      <div className="w-full max-w-xl mt-10">
        <h2 className="text-xl font-semibold mb-3">Single-Ticker Forecast</h2>

        <div className="flex flex-col md:flex-row items-center gap-4 mb-6">
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            placeholder="Enter Ticker (e.g., AAPL)"
            className="p-3 border border-gray-300 rounded-md w-64 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="number"
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            placeholder="Days"
            className="p-3 border border-gray-300 rounded-md w-32 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            min={1}
          />
          <button
            onClick={fetchPrediction}
            className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition disabled:opacity-50"
            disabled={loading}
          >
            {loading ? 'Predicting…' : 'Predict'}
          </button>
        </div>

        {loading && <p className="text-gray-500 animate-pulse">Working…</p>}

        {forecast.length > 0 && (
          <div className="w-full mt-6">
            <h3 className="text-lg font-semibold mb-4">Forecast Table</h3>
            <table className="w-full table-auto border border-gray-300 shadow-sm bg-white rounded-md mb-6">
              <thead className="bg-gray-200">
                <tr>
                  <th className="border p-2">Date</th>
                  <th className="border p-2">Predicted Price</th>
                </tr>
              </thead>
              <tbody>
                {forecast.map((entry, index) => (
                  <tr key={index} className="text-center">
                    <td className="border p-2">{String(entry.ds).split('T')[0]}</td>
                    <td className="border p-2">{entry.yhat.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <h3 className="text-lg font-semibold mb-2">📈 Forecast Chart</h3>
            <Line
              data={{
                labels: forecast.map((f) => String(f.ds).split('T')[0]),
                datasets: [
                  {
                    label: `Prediction for ${ticker.toUpperCase()}`,
                    data: forecast.map((f) => f.yhat),
                    fill: false,
                    tension: 0.3,
                  },
                ],
              }}
              options={{
                responsive: true,
                plugins: { legend: { position: 'top' } },
              }}
            />

            <div className="mt-6 bg-white shadow p-4 rounded-md">
              <h3 className="text-lg font-semibold mb-2">AI Explanation</h3>
              <p className="text-gray-700 whitespace-pre-line">{explanation}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
