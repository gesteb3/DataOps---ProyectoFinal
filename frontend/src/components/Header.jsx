import { API_URL } from "../api/client";

const engines = ["Todos", "SQL Server", "Oracle", "PostgreSQL"];

function Header({
  loading,
  onRefresh,
  onLogout,
  onResolveAll,
  pendingAlerts,
  globalFilter,
  databaseOptions,
  onFilterChange
}) {
  const selectedMotor = globalFilter?.motor || "Todos";
  const selectedDatabase = globalFilter?.databaseName || "Todas";

  const handleMotorChange = (event) => {
    onFilterChange({
      motor: event.target.value,
      databaseName: "Todas"
    });
  };

  const handleDatabaseChange = (event) => {
    onFilterChange({
      motor: selectedMotor,
      databaseName: event.target.value
    });
  };

  return (
    <header className="topbar">
      <div className="topbar-title">
        <p className="eyebrow">Dashboard administrativo</p>
        <h1>DataOps Control Center</h1>
        <span className="api-url">Backend: {API_URL}</span>
      </div>

      <div className="global-filter" aria-label="Filtro global del dashboard">
        <div>
          <label>Seleccionar Motor</label>
          <select value={selectedMotor} onChange={handleMotorChange} disabled={loading}>
            {engines.map((engine) => (
              <option key={engine} value={engine}>{engine}</option>
            ))}
          </select>
        </div>

        <div>
          <label>Seleccionar Base de Datos</label>
          <select value={selectedDatabase} onChange={handleDatabaseChange} disabled={loading}>
            <option value="Todas">Todas</option>
            {(databaseOptions || []).map((databaseName) => (
              <option key={databaseName} value={databaseName}>{databaseName}</option>
            ))}
          </select>
        </div>
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
