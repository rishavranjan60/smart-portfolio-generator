import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [ticker, setTicker] = useState('');
  const [days, setDays] = useState(30);
  const [result, setResult] = useState([]);

  const predict = async () => {
    const res = await axios.post('http://<EC2_PUBLIC_IP>:8000/api/predict', { ticker, days });
    setResult(res.data);
  };

  return (
    <div>
      <h1>Smart Portfolio Generator</h1>
      <input value={ticker} onChange={(e) => setTicker(e.target.value)} placeholder="Enter Ticker (e.g., AAPL)" />
      <input type="number" value={days} onChange={(e) => setDays(Number(e.target.value))} />
      <button onClick={predict}>Forecast</button>
      <pre>{JSON.stringify(result, null, 2)}</pre>
    </div>
  );
}

export default App;
