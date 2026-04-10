import ZoneCell from './ZoneCell';

function HeatmapGrid({ zones, route }) {
  const pathSet = new Set(route?.path || []);
  const start = route?.path?.[0] || null;
  const end = route?.path?.[route.path.length - 1] || null;

  const gridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(5, 1fr)',
    gap: '10px',
    padding: '20px',
  };

  return (
    <div className="heatmap-grid" style={gridStyle}>
      {zones.map(z => (
        <ZoneCell
          key={z.id}
          zone={z}
          isOnPath={pathSet.has(z.id)}
          isStart={z.id === start}
          isEnd={z.id === end}
        />
      ))}
    </div>
  );
}

export default HeatmapGrid;
