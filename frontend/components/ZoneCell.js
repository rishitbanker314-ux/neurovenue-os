function ZoneCell({ zone, isOnPath, isStart, isEnd }) {
  // Density-based color: green (low) → yellow → orange → red (high)
  const density = zone.density;
  let r, g, b;

  if (density <= 30) {
    r = Math.round((density / 30) * 255);
    g = 200;
    b = 50;
  } else if (density <= 60) {
    r = 255;
    g = Math.round(200 - ((density - 30) / 30) * 150);
    b = 50;
  } else {
    r = 255;
    g = Math.round(50 - ((density - 60) / 40) * 50);
    b = Math.round(50 - ((density - 60) / 40) * 30);
  }

  const bgColor = `rgba(${r}, ${g}, ${b}, ${0.3 + (density / 100) * 0.5})`;
  const textColor = `rgb(${r}, ${g}, ${b})`;

  // Border for route path
  let borderStyle = '2px solid transparent';
  if (isStart) borderStyle = '2px solid #34d399';
  else if (isEnd) borderStyle = '2px solid #f472b6';
  else if (isOnPath) borderStyle = '2px solid #818cf8';

  const style = {
    backgroundColor: bgColor,
    color: textColor,
    border: borderStyle,
    borderRadius: '12px',
    padding: '12px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '4px',
    cursor: 'pointer',
    transition: 'all 0.4s ease',
    position: 'relative',
    aspectRatio: '1',
  };

  return (
    <div style={style} className="zone-cell">
      <span style={{ fontWeight: 700, fontSize: '13px', fontFamily: 'monospace' }}>
        {zone.id}
      </span>
      <span style={{ fontWeight: 800, fontSize: '20px', fontFamily: 'monospace' }}>
        {density}
      </span>
      <span style={{ fontSize: '10px', opacity: 0.7 }}>
        {zone.avg_speed} m/s
      </span>
      {isStart && <span style={{ position: 'absolute', top: 4, right: 6, fontSize: '10px' }}>START</span>}
      {isEnd && <span style={{ position: 'absolute', top: 4, right: 6, fontSize: '10px' }}>END</span>}
    </div>
  );
}

export default ZoneCell;
