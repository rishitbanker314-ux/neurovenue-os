import { useState, useEffect, useCallback } from 'react';
import HeatmapGrid from './components/HeatmapGrid';
import RouteOverlay from './components/RouteOverlay';
import NotificationPanel from './components/NotificationPanel';
import PredictionsPanel from './components/PredictionsPanel';
import ControlPanel from './components/ControlPanel';
import ScenarioControls from './components/ScenarioControls';

const API_BASE = 'http://localhost:5050';
const REFRESH_INTERVAL = 3000;

function App() {
  const [zones, setZones] = useState([]);
  const [route, setRoute] = useState({ path: [], time_saved: 0 });
  const [nudge, setNudge] = useState('');
  const [nudgeHistory, setNudgeHistory] = useState([]);
  const [start, setStart] = useState('A1');
  const [end, setEnd] = useState('E5');
  const [tick, setTick] = useState(0);
  const [phase, setPhase] = useState('—');
  const [connected, setConnected] = useState(false);
  const [predictions, setPredictions] = useState(null);

  // Fetch live state from simulation engine API
  const fetchState = useCallback(async (s, e) => {
    try {
      const res = await fetch(`${API_BASE}/api/state?s=${s || start}&e=${e || end}`);
      const data = await res.json();

      // Update zone data (drives HeatmapGrid)
      setZones(data.zones);

      // Update routing output (drives RouteOverlay)
      setRoute(data.route);

      // Update nudge message (drives NotificationPanel)
      setNudge(data.nudge);

      // Append to nudge history for real-time suggestion feed
      setNudgeHistory(prev => {
        const entry = { text: data.nudge, time: new Date().toLocaleTimeString() };
        const updated = [entry, ...prev];
        return updated.slice(0, 10); // Keep latest 10
      });

      // Update metadata
      setTick(data.tick);
      setPhase(data.phase);
      setPredictions(data.predictions);
      setConnected(true);
    } catch (err) {
      console.error('API fetch failed:', err);
      setConnected(false);
    }
  }, [start, end]);

  // Auto-refresh every 3 seconds — core connection to simulation engine
  useEffect(() => {
    fetchState();
    const interval = setInterval(() => {
      fetchState();
    }, 3000);
    return () => clearInterval(interval);
  }, [fetchState]);

  // Route change handler — updates start/end and fetches immediately
  const handleRouteChange = (newStart, newEnd) => {
    setStart(newStart);
    setEnd(newEnd);
    fetchState(newStart, newEnd);
  };

  // Scenario change handler — POSTs to API and fetches immediately
  const handleScenarioChange = async (scenario) => {
    try {
      await fetch(`${API_BASE}/api/scenario`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario })
      });
      fetchState();
    } catch (err) {
      console.error('Scenario update failed:', err);
    }
  };

  // Compute stats from live zone data
  const avgDensity = zones.length > 0
    ? Math.round(zones.reduce((s, z) => s + z.density, 0) / zones.length)
    : 0;
  const hotZones = zones.filter(z => z.density > 80).length;

  return (
    <main className="app">
      {/* Header with connection status */}
      <header className="app-header" role="banner">
        <h1>NeuroVenue OS</h1>
        <div className="status" aria-live="polite">
          <span className={`dot ${connected ? 'connected' : 'disconnected'}`} />
          {connected ? `Tick ${tick} · ${phase}` : 'Disconnected'}
        </div>
      </header>

      {/* Stats bar */}
      <section className="stats-bar" aria-live="polite" aria-label="Live Simulation Metrics" style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '16px', marginBottom: '28px' }}>
        <div className="stat" style={{ padding: '20px', background: 'rgba(255,255,255,0.05)', borderRadius: '16px' }}>Avg Density: <strong>{avgDensity}</strong></div>
        <div className="stat" style={{ padding: '20px', background: 'rgba(255,255,255,0.05)', borderRadius: '16px' }}>Hot Zones: <strong>{hotZones}</strong></div>
        <div className="stat" style={{ padding: '20px', background: 'rgba(255,255,255,0.05)', borderRadius: '16px' }}>Time Saved: <strong>{route.time_saved}s</strong></div>
        <div className="stat" style={{ padding: '20px', background: 'rgba(255,255,255,0.05)', borderRadius: '16px' }}>Confidence: <strong style={{ color: '#6366f1' }}>{Math.min(99, Math.max(82, 98 - (hotZones * 2) - (route.path.length * 1)))}%</strong></div>
      </section>

      {/* Scenario controls */}
      <section aria-label="Crowd Scenario Controls">
        <ScenarioControls onScenarioChange={handleScenarioChange} />
      </section>

      {/* Route controls */}
      <section aria-label="Routing Controls">
        <ControlPanel onRouteChange={handleRouteChange} />
      </section>

      {/* Grid rendering entirely semantic constraints explicitly bypassing plain divs natively */}
      <section aria-label="Live Venue Simulation Visualization">
        <HeatmapGrid zones={zones} route={route} />
        <RouteOverlay route={route} />
      </section>

      <aside aria-label="Predictive Hazards Engine">
        <PredictionsPanel predictions={predictions} />
      </aside>

      <aside aria-label="System Notifications">
        <NotificationPanel message={nudge} history={nudgeHistory} />
      </aside>
    </main>
  );
}

export default App;
