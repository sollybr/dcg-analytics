export default function AnalyticsChart({ title, children }) {
  return (
    <div className="digi-card">
      <div className="card-header">
        {title}
      </div>

      <div className="chart-container">
        {children}
      </div>
    </div>
  );
}