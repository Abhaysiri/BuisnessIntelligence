import React, { useState } from 'react';
import axios from 'axios';
import { VegaEmbed } from 'react-vega';
import './App.css';

function App() {
  const [visualizations, setVisualizations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchVisualizations = async () => {
    setLoading(true);
    setError(null);
    try {
      // Mock data that mirrors kpi-engine payload with metadata additions
      const mockPayload = {
        incident_id: "test-123",
        kpi_id: "revenue_weekly",
        observed_value: 850000,
        expected_value: 900000,
        percentage_change: -5.55,
        drivers: [
          {
            name: "Conversion Rate Drop in Europe",
            contribution_absolute: -40000,
            contribution_percentage: -4.44,
            diagnostic_confidence: 0.92
          },
          {
            name: "Traffic Drop in Asia",
            contribution_absolute: -8000,
            contribution_percentage: -0.88,
            diagnostic_confidence: 0.85
          }
        ],
        metadata: {
          trend_data: Array.from({ length: 30 }).map((_, i) => ({
            timestamp: new Date(Date.now() - (30 - i) * 86400000).toISOString(),
            actual_value: 1000 - (30 - i) * 10 + ((30 - i) % 3 * 5),
            expected_value: 1050 - (30 - i) * 10,
            lower_bound: 1020 - (30 - i) * 10,
            upper_bound: 1080 - (30 - i) * 10
          })),
          dimensions: [
            { dimension: "Europe", value: -40000 },
            { dimension: "Asia", value: -8000 },
            { dimension: "US", value: -5000 }
          ],
          events: [
            {
              timestamp: new Date(Date.now() - 15 * 86400000).toISOString(),
              event_type: "Marketing",
              title: "Summer Sale"
            },
            {
              timestamp: new Date(Date.now() - 5 * 86400000).toISOString(),
              event_type: "Outage",
              title: "Payment Gateway Down"
            }
          ]
        }
      };

      const response = await axios.post('http://localhost:8001/visualizations', mockPayload);
      setVisualizations(response.data);
    } catch (err) {
      console.error(err);
      setError('Failed to fetch visualizations from API. Is the Python backend running on port 8001?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>KPI Engine Visualizations</h1>
        <button onClick={fetchVisualizations} disabled={loading} style={{ padding: '10px 20px', fontSize: '16px', cursor: 'pointer' }}>
          {loading ? 'Loading...' : 'Generate Story'}
        </button>
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </header>
      
      <main className="App-main" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '40px', maxWidth: '1000px', margin: '0 auto' }}>
        {visualizations.map((spec, index) => (
          <div key={index} className="Visualization-card" style={{ border: '1px solid #ccc', padding: '20px', borderRadius: '8px', background: '#fff' }}>
            <h2 style={{ marginTop: 0 }}>{spec.name}</h2>
            <p style={{ color: '#666', marginBottom: '20px' }}>{spec.description}</p>
            <VegaEmbed spec={spec.vega_lite_spec} options={{ actions: false }} />
          </div>
        ))}
      </main>
    </div>
  );
}

export default App;
