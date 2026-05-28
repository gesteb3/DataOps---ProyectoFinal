function ChartCard({ title, subtitle, error, loading, children, action }) {
  return (
    <section className="chart-card">
      <div className="section-heading">
        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {action}
      </div>

      {loading && <div className="panel-state">Cargando datos...</div>}
      {!loading && error && <div className="section-error">{error}</div>}
      {!loading && !error && children}
    </section>
  );
}

export default ChartCard;
