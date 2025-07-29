import { useState } from 'react';

import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend);

function App() {
  const [ticker, setTicker] = useState('');
  const [days, setDays] = useState(5);
  const [forecast, setForecast] = useState([]);
  const [explanation, setExplanation] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchPrediction = async () => {
    setLoading(true);
    setForecast([]);
    setExplanation('');

    try {
      //const response = await fetch('http://127.0.0.1:8000/predict', {
        const response = await fetch('https://6zy9b4ec22.execute-api.eu-central-1.amazonaws.com/dev/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker, days }),
      });

      const data = await response.json();
      setForecast(data.forecast || []);
      setExplanation(data.explanation || 'No explanation provided.');
    } catch (error) {
      console.error('API Error:', error);
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
      <h1 className="text-3xl font-bold mb-6">📈 Smart Portfolio Predictor</h1>

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
        />
        <button
          onClick={fetchPrediction}
          className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition disabled:opacity-50"
          disabled={loading}
        >
          {loading ? 'Predicting...' : 'Predict'}
        </button>
      </div>

      {loading && <p className="text-gray-500 animate-pulse">Fetching prediction...</p>}

      {forecast.length > 0 && (
        <div className="w-full max-w-xl mt-6">
          <h2 className="text-lg font-semibold mb-4">📊 Forecast Table</h2>

          <table className="w-full table-auto border border-gray-300 shadow-sm bg-white rounded-md mb-6">
            <thead className="bg-gray-200">
              <tr>
                <th className="border p-2">Date</th>
                <th className="border p-2">Predicted Price (USD)</th>
              </tr>
            </thead>
            <tbody>
              {forecast.map((entry: any, index: number) => (
                <tr key={index} className="text-center">
                  <td className="border p-2">{entry.ds.split('T')[0]}</td>
                  <td className="border p-2">{entry.yhat.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <h2 className="text-lg font-semibold mb-2">📈 Forecast Chart</h2>
          <Line
            data={{
              labels: forecast.map((f: any) => f.ds.split('T')[0]),
              datasets: [
                {
                  label: `Prediction for ${ticker.toUpperCase()}`,
                  data: forecast.map((f: any) => f.yhat),
                  fill: false,
                  borderColor: 'rgba(59, 130, 246, 1)',
                  backgroundColor: 'rgba(59, 130, 246, 0.2)',
                  tension: 0.3,
                },
              ],
            }}
            options={{
              responsive: true,
              plugins: {
                legend: {
                  position: 'top' as const,
                },
              },
            }}
          />

          <div className="mt-6 bg-white shadow p-4 rounded-md">
            <h2 className="text-lg font-semibold mb-2">🧠 AI Explanation</h2>
            <p className="text-gray-700 whitespace-pre-line">{explanation}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
