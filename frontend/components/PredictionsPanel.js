import React from 'react';

function PredictionsPanel({ predictions }) {
  if (!predictions) {
    return null;
  }

  const hasPredictions = 
    (predictions.plus_5s && predictions.plus_5s.length > 0) ||
    (predictions.plus_10s && predictions.plus_10s.length > 0) ||
    (predictions.plus_20s && predictions.plus_20s.length > 0);

  if (!hasPredictions) {
    return null; // Don't show anything if no future risks are detected
  }

  return (
    <div className="predictions-panel" style={{
      marginTop: '20px',
      padding: '16px',
      borderRadius: '12px',
      background: 'rgba(249, 115, 22, 0.1)',
      border: '1px solid rgba(249, 115, 22, 0.3)'
    }}>
      <h3 style={{ 
        color: '#f97316', 
        marginBottom: '12px', 
        fontFamily: 'monospace',
        textTransform: 'uppercase',
        fontSize: '14px',
        letterSpacing: '1px'
      }}>
        🔮 Predicted Congestion Zones
      </h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
        {/* +5 Seconds */}
        <div style={{ padding: '10px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '6px' }}>+5 SECONDS</div>
          {predictions.plus_5s && predictions.plus_5s.length > 0 ? (
            <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
              {predictions.plus_5s.map(zone => (
                <span key={zone} style={{ background: '#f97316', color: '#fff', padding: '2px 6px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold' }}>{zone}</span>
              ))}
            </div>
          ) : (
            <span style={{ fontSize: '12px', color: '#475569' }}>Clear</span>
          )}
        </div>

        {/* +10 Seconds */}
        <div style={{ padding: '10px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '6px' }}>+10 SECONDS</div>
          {predictions.plus_10s && predictions.plus_10s.length > 0 ? (
            <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
              {predictions.plus_10s.map(zone => (
                <span key={zone} style={{ background: '#ef4444', color: '#fff', padding: '2px 6px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold' }}>{zone}</span>
              ))}
            </div>
          ) : (
            <span style={{ fontSize: '12px', color: '#475569' }}>Clear</span>
          )}
        </div>

        {/* +20 Seconds */}
        <div style={{ padding: '10px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '6px' }}>+20 SECONDS</div>
          {predictions.plus_20s && predictions.plus_20s.length > 0 ? (
            <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
              {predictions.plus_20s.map(zone => (
                <span key={zone} style={{ background: '#b91c1c', color: '#fff', padding: '2px 6px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold' }}>{zone}</span>
              ))}
            </div>
          ) : (
            <span style={{ fontSize: '12px', color: '#475569' }}>Clear</span>
          )}
        </div>
      </div>
    </div>
  );
}

export default PredictionsPanel;
