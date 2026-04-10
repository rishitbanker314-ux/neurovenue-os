function NotificationPanel({ message, history = [] }) {
  return (
    <div className="notification-panel">
      {/* Current nudge — large display */}
      <div className="current-nudge">
        <h3>💡 Live Suggestion</h3>
        <p>{message || 'Waiting for data...'}</p>
      </div>

      {/* Nudge history — scrollable feed */}
      {history.length > 0 && (
        <div className="nudge-history">
          <h4>📋 Recent Nudges</h4>
          <ul>
            {history.map((entry, i) => (
              <li key={i}>
                <span className="nudge-text">{entry.text}</span>
                <span className="nudge-time">{entry.time}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default NotificationPanel;
