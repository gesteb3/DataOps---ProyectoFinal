function StatCard({ title, value, subtitle, tone = "blue", icon = "•" }) {
  return (
    <article className={`stat-card stat-${tone}`}>
      <div className="stat-icon">{icon}</div>
      <div>
        <span>{title}</span>
        <strong>{value}</strong>
        {subtitle && <small>{subtitle}</small>}
      </div>
    </article>
  );
}

export default StatCard;
