import { API_URL } from "../api/client";

function Header({ loading, onRefresh, onLogout, onResolveAll, pendingAlerts }) {
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">Dashboard administrativo</p>
        <h1>DataOps Control Center</h1>
        <span className="api-url">Backend: {API_URL}</span>
      </div>

      <div className="topbar-actions">
        <button className="btn btn-danger" onClick={onResolveAll} disabled={loading || pendingAlerts === 0}>
          Resolver alertas {pendingAlerts > 0 ? `(${pendingAlerts})` : ""}
        </button>
        <button className="btn btn-primary" onClick={onRefresh} disabled={loading}>
          {loading ? "Actualizando..." : "Actualizar dashboard"}
        </button>
        <button className="btn btn-ghost" onClick={onLogout}>
          Cerrar sesión
        </button>
      </div>
    </header>
  );
}

export default Header;
