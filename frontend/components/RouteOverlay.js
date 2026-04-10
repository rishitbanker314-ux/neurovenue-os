function RouteOverlay({ route }) {
  if (!route || !route.path || route.path.length === 0) {
    return null;
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  return (
    <div className="route-overlay">
      <h3>🧭 Recommended Route</h3>

      {/* Visual path */}
      <div className="route-path" style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' }}>
        {route.path.map((zone, i) => {
          const isFirst = i === 0;
          const isLast = i === route.path.length - 1;

          const nodeStyle = {
            padding: '6px 12px',
            borderRadius: '8px',
            fontFamily: 'monospace',
            fontWeight: 600,
            fontSize: '13px',
            background: isFirst ? 'rgba(52,211,153,0.15)' : isLast ? 'rgba(244,114,182,0.15)' : 'rgba(129,140,248,0.15)',
            color: isFirst ? '#34d399' : isLast ? '#f472b6' : '#818cf8',
            border: `1px solid ${isFirst ? 'rgba(52,211,153,0.3)' : isLast ? 'rgba(244,114,182,0.3)' : 'rgba(129,140,248,0.3)'}`,
          };

          return (
            <span key={zone}>
              <span style={nodeStyle}>{zone}</span>
              {!isLast && <span style={{ color: '#64748b', margin: '0 2px' }}> → </span>}
            </span>
          );
        })}
      </div>

      {/* Time saved */}
      <div style={{
        marginTop: '12px',
        padding: '10px 16px',
        borderRadius: '10px',
        background: 'rgba(16,185,129,0.12)',
        border: '1px solid rgba(16,185,129,0.2)',
        color: '#10b981',
        fontWeight: 600,
        fontSize: '14px',
      }}>
        ⚡ {formatTime(route.time_saved)} saved via smart route
      </div>
    </div>
  );
}

export default RouteOverlay;
