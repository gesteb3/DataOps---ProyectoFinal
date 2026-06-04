import { useMemo, useState } from "react";
import { API_URL } from "../api/client";

const engineOptions = ["PostgreSQL", "SQL Server", "Oracle"];
const backupTypes = ["FULL", "DIFF", "INC"];

function buildConnectionLabel(connection) {
  return `${connection.database_name} · ${connection.nombre || connection.motor}`;
}

function MultiSelectDropdown({ label, placeholder, options, selectedValues, onChange, getLabel, getValue, disabled }) {
  const [open, setOpen] = useState(false);

  const selectedSet = useMemo(() => new Set(selectedValues), [selectedValues]);
  const selectedLabels = useMemo(
    () => options
      .filter((option) => selectedSet.has(getValue(option)))
      .map((option) => getLabel(option)),
    [options, selectedSet, getLabel, getValue]
  );

  const toggleValue = (value) => {
    if (selectedSet.has(value)) {
      onChange(selectedValues.filter((item) => item !== value));
      return;
    }

    onChange([...selectedValues, value]);
  };

  const selectAll = () => {
    onChange(options.map((option) => getValue(option)));
  };

  const clearAll = () => {
    onChange([]);
  };

  return (
    <div className="filter-dropdown">
      <span className="filter-label">{label}</span>

      <button
        className={`filter-trigger ${open ? "active" : ""}`}
        type="button"
        disabled={disabled}
        onClick={() => setOpen((current) => !current)}
      >
        <span>{selectedLabels.length ? `${selectedLabels.length} seleccionado(s)` : placeholder}</span>
        <strong>⌄</strong>
      </button>

      {open && (
        <div className="filter-menu">
          <div className="filter-menu-actions">
            <button type="button" onClick={selectAll}>Todos</button>
            <button type="button" onClick={clearAll}>Limpiar</button>
          </div>

          <div className="filter-options">
            {options.length === 0 ? (
              <p className="filter-empty">No hay opciones registradas.</p>
            ) : (
              options.map((option) => {
                const value = getValue(option);
                const checked = selectedSet.has(value);

                return (
                  <label className="filter-option" key={value}>
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleValue(value)}
                    />
                    <span>{getLabel(option)}</span>
                  </label>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Header({
  loading,
  onRefresh,
  onLogout,
  onResolveAll,
  pendingAlerts,
  connections = [],
  filters,
  onFilterChange,
  onRunBackup,
  backupRunning
}) {
  const selectedEngineSet = useMemo(() => new Set(filters.engines), [filters.engines]);

  const databaseOptions = useMemo(() => {
    const filtered = filters.engines.length
      ? connections.filter((connection) => selectedEngineSet.has(connection.motor))
      : connections;

    return filtered.map((connection) => ({
      ...connection,
      value: Number(connection.connection_id || connection.id)
    }));
  }, [connections, filters.engines, selectedEngineSet]);

  const selectedDatabases = useMemo(() => {
    const validIds = new Set(databaseOptions.map((connection) => Number(connection.value)));
    return filters.connectionIds.filter((id) => validIds.has(Number(id)));
  }, [databaseOptions, filters.connectionIds]);

  const updateEngines = (engines) => {
    const validConnections = connections
      .filter((connection) => engines.length === 0 || engines.includes(connection.motor))
      .map((connection) => Number(connection.connection_id || connection.id));

    const validSet = new Set(validConnections);

    onFilterChange({
      engines,
      connectionIds: filters.connectionIds.filter((id) => validSet.has(Number(id)))
    });
  };

  const updateConnectionIds = (connectionIds) => {
    onFilterChange({
      ...filters,
      connectionIds: connectionIds.map(Number)
    });
  };

  const selectedSummary = useMemo(() => {
    if (filters.connectionIds.length > 0) {
      return `${filters.connectionIds.length} base(s) seleccionada(s)`;
    }

    if (filters.engines.length > 0) {
      return `${filters.engines.length} motor(es) seleccionados`;
    }

    return "Todos los motores y bases";
  }, [filters.connectionIds.length, filters.engines.length]);

  return (
    <header className="topbar topbar-enhanced">
      <div className="topbar-title-block">
        <p className="eyebrow">Dashboard administrativo</p>
        <h1>DataOps Control Center</h1>
        <span className="api-url">Backend: {API_URL}</span>
      </div>

      <section className="global-filter-card" aria-label="Filtro global de motores y bases de datos">
        <div className="global-filter-head">
          <div>
            <span>Filtro Global</span>
            <strong>{selectedSummary}</strong>
          </div>
          <button
            type="button"
            className="filter-clear"
            onClick={() => onFilterChange({ engines: [], connectionIds: [] })}
          >
            Limpiar
          </button>
        </div>

        <div className="filter-row">
          <MultiSelectDropdown
            label="Seleccionar Motor"
            placeholder="Todos los motores"
            options={engineOptions}
            selectedValues={filters.engines}
            onChange={updateEngines}
            getLabel={(option) => option}
            getValue={(option) => option}
          />

          <MultiSelectDropdown
            label="Seleccionar Base de Datos"
            placeholder="Todas las bases"
            options={databaseOptions}
            selectedValues={selectedDatabases}
            onChange={updateConnectionIds}
            getLabel={buildConnectionLabel}
            getValue={(option) => Number(option.value)}
            disabled={connections.length === 0}
          />
        </div>

        <div className="backup-action-strip">
          <span>Backup para selección:</span>
          {backupTypes.map((type) => (
            <button
              key={type}
              type="button"
              className="backup-type-button"
              disabled={backupRunning || loading}
              onClick={() => onRunBackup(type)}
            >
              {backupRunning ? "..." : type}
            </button>
          ))}
        </div>
      </section>

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
