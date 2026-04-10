import { useState } from 'react';

function ControlPanel({ onRouteChange }) {
  const [start, setStart] = useState('A1');
  const [end, setEnd] = useState('E5');

  const handleSubmit = (e) => {
    e.preventDefault();
    onRouteChange(start.toUpperCase(), end.toUpperCase());
  };

  return (
    <div className="control-panel">
      <h3>🎮 Route Control</h3>
      <form onSubmit={handleSubmit}>
        <div className="control-inputs">
          <input
            type="text"
            value={start}
            onChange={(e) => setStart(e.target.value)}
            placeholder="Start (e.g. A1)"
            maxLength={2}
          />
          <span className="control-arrow">→</span>
          <input
            type="text"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
            placeholder="End (e.g. E5)"
            maxLength={2}
          />
          <button type="submit">Find Route</button>
        </div>
      </form>
    </div>
  );
}

export default ControlPanel;
