import { useState } from 'react';

function ScenarioControls({ onScenarioChange }) {
  const [active, setActive] = useState('auto');

  const handleScenario = (scenario) => {
    setActive(scenario);
    onScenarioChange(scenario);
  };

  return (
    <div className="control-panel" style={{ marginBottom: '16px' }}>
      <h3>🎬 Scenario Controls</h3>
      <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
        <button 
          onClick={() => handleScenario('auto')}
          style={{ padding: '8px 12px', background: active === 'auto' ? '#6366f1' : '#1a1f2e', color: 'white', border: '1px solid #333', borderRadius: '8px', cursor: 'pointer' }}
        >
          Auto Mode
        </button>
        <button 
          onClick={() => handleScenario('entry')}
          style={{ padding: '8px 12px', background: active === 'entry' ? '#6366f1' : '#1a1f2e', color: 'white', border: '1px solid #333', borderRadius: '8px', cursor: 'pointer' }}
        >
          Entry Rush
        </button>
        <button 
          onClick={() => handleScenario('halftime')}
          style={{ padding: '8px 12px', background: active === 'halftime' ? '#6366f1' : '#1a1f2e', color: 'white', border: '1px solid #333', borderRadius: '8px', cursor: 'pointer' }}
        >
          Halftime
        </button>
        <button 
          onClick={() => handleScenario('emergency')}
          style={{ padding: '8px 12px', background: active === 'emergency' ? '#ef4444' : '#1a1f2e', color: active === 'emergency' ? 'white' : '#ef4444', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', cursor: 'pointer' }}
        >
          Evacuation
        </button>
      </div>
    </div>
  );
}

export default ScenarioControls;
