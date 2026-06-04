import { useEffect, useMemo, useState } from "react";
import { api, API_URL } from "../api/client";

const ENGINE_CONFIG = {
  PostgreSQL: {
    label: "PostgreSQL",
    port: 5432,
    hostPlaceholder: "postgres o localhost",
    dbPlaceholder: "dataops_db",
    userPlaceholder: "dataops"
  },
  "SQL Server": {
    label: "SQL Server",
    port: 1433,
    hostPlaceholder: "host.docker.internal o IP del servidor",
    dbPlaceholder: "master",
    userPlaceholder: "sa"
  },
  Oracle: {
    label: "Oracle",
    port: 1521,
    hostPlaceholder: "host.docker.internal o IP del servidor",
    dbPlaceholder: "XEPDB1 o ORCLPDB1",
    userPlaceholder: "system"
  }
};

const directEndpoints = [
  { label: "Simular concurrencia", method: "POST", path: "/concurrency/simulate" },
  { label: "Deadlock real PostgreSQL", method: "POST", path: "/concurrency/real-deadlock-postgres" },
  { label: "Listar conexiones", method: "GET", path: "/connections" },
  { label: "Simular desastre", method: "POST", path: "/backup/simulate-disaster" },
  { label: "Restaurar backup", method: "POST", path: "/backup/restore" },
  { label: "Evaluar alertas", method: "POST", path: "/alerts/evaluate" },
  { label: "Replicación normal 2s", method: "POST", path: "/replication/simulate/normal" },
  { label: "Replicación media 5s", method: "POST", path: "/replication/simulate/media" },
  { label: "Replicación alta 20s", method: "POST", path: "/replication/simulate/alta" },
  { label: "Backup full", method: "POST", path: "/backup/full" },
  { label: "Backup diferencial", method: "POST", path: "/backup/diff" },
  { label: "Backup incremental", method: "POST", path: "/backup/inc" },
  { label: "Inicializar reglas", method: "POST", path: "/alerts/init-rules" },
  { label: "Resolver alertas", method: "PUT", path: "/alerts/resolve-all" }
];

const parameterizedEndpoints = [
  {
    key: "invalidate-cache",
    label: "Invalidar caché",
    method: "DELETE",
    pathTemplate: "/cache/invalidate/{query_key}",
    inputName: "query_key",
    placeholder: "query_key"
  },
  {
    key: "test-connection-by-id",
    label: "Probar conexión guardada por ID",
    method: "POST",
    pathTemplate: "/connections/{connection_id}/test",
    inputName: "connection_id",
    placeholder: "connection_id"
  },
  {
    key: "delete-connection-by-id",
    label: "Eliminar conexión por ID",
    method: "DELETE",
    pathTemplate: "/connections/{connection_id}",
    inputName: "connection_id",
    placeholder: "connection_id"
  },
  {
    key: "get-cache-query",
    label: "Consultar caché",
    method: "GET",
    pathTemplate: "/cache/query/{query_key}",
    inputName: "query_key",
    placeholder: "query_key"
  }
];

const initialConsole = {
  status: "idle",
  title: "Listo para ejecutar pruebas",
  detail: "Selecciona un endpoint para ver aquí la respuesta del backend.",
  method: "",
  path: "",
  payload: null
};

const initialConnectionForm = {
  nombre: "PostgreSQL Local",
  motor: "PostgreSQL",
  host: "postgres",
  port: 5432,
  database_name: "dataops_db",
  user_name: "dataops",
  password: "dataops123"
};

function buildPath(pathTemplate, inputName, value) {
  return pathTemplate.replace(`{${inputName}}`, encodeURIComponent(value.trim()));
}

function formatPayload(payload) {
  if (payload === null || payload === undefined) return "Sin respuesta";

  try {
    return JSON.stringify(payload, null, 2);
  } catch {
    return String(payload);
  }
}

function getErrorPayload(error) {
  if (error?.response) {
    return error.response.data || {
      message: "El backend respondió con error.",
      status: error.response.status
    };
  }

  if (error?.request) {
    return {
      message: "No hubo respuesta del backend. Verifica que la API esté encendida.",
      backend: API_URL
    };
  }

  return {
    message: error?.message || "Error inesperado al ejecutar la prueba."
  };
}

function DemoPanel({ open, onClose, onAfterRun }) {
  const [consoleState, setConsoleState] = useState(initialConsole);
  const [runningKey, setRunningKey] = useState("");
  const [showConnectionModal, setShowConnectionModal] = useState(false);
  const [connectionForm, setConnectionForm] = useState(initialConnectionForm);
  const [savedConnections, setSavedConnections] = useState([]);
  const [loadingConnections, setLoadingConnections] = useState(false);

  const [params, setParams] = useState({
    "invalidate-cache": "",
    "test-connection-by-id": "",
    "delete-connection-by-id": "",
    "get-cache-query": ""
  });

  const isRunning = Boolean(runningKey);
  const selectedEngineConfig = ENGINE_CONFIG[connectionForm.motor] || ENGINE_CONFIG.PostgreSQL;

  const panelTitle = useMemo(() => {
    if (isRunning) return "Ejecutando prueba...";
    return "Demo/Pruebas API";
  }, [isRunning]);

  useEffect(() => {
    if (!open) return undefined;

    const handleEscape = (event) => {
      if (event.key === "Escape") {
        if (showConnectionModal) {
          setShowConnectionModal(false);
          return;
        }
        onClose();
      }
    };

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [open, onClose, showConnectionModal]);

  useEffect(() => {
    if (open) {
      loadConnections();
    }
  }, [open]);

  const refreshDashboard = () => {
    if (typeof onAfterRun === "function") {
      onAfterRun();
    }
  };

  const executeRequest = async ({ key, label, method, path, data }) => {
    const requestKey = key || `${method}-${path}`;
    const startedAt = performance.now();

    setRunningKey(requestKey);
    setConsoleState({
      status: "loading",
      title: `Ejecutando: ${label}`,
      detail: "Esperando respuesta del backend...",
      method,
      path,
      payload: null
    });

    try {
      const requestConfig = {
        method,
        url: path
      };

      if (data !== undefined && data !== null) {
        requestConfig.data = data;
      }

      const response = await api.request(requestConfig);
      const duration = Math.round(performance.now() - startedAt);

      setConsoleState({
        status: "success",
        title: "Ejecución exitosa",
        detail: `HTTP ${response.status} · ${duration} ms`,
        method,
        path,
        payload: response.data
      });

      refreshDashboard();
      return response.data;
    } catch (error) {
      const duration = Math.round(performance.now() - startedAt);
      const status = error?.response?.status;

      setConsoleState({
        status: "error",
        title: "La prueba devolvió error",
        detail: `${status ? `HTTP ${status}` : "Sin respuesta HTTP"} · ${duration} ms`,
        method,
        path,
        payload: getErrorPayload(error)
      });

      return null;
    } finally {
      setRunningKey("");
    }
  };

  const loadConnections = async () => {
    setLoadingConnections(true);

    try {
      const response = await api.get("/connections");
      setSavedConnections(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      setConsoleState({
        status: "error",
        title: "No se pudieron cargar las conexiones",
        detail: error?.response?.status ? `HTTP ${error.response.status}` : "Sin respuesta HTTP",
        method: "GET",
        path: "/connections",
        payload: getErrorPayload(error)
      });
    } finally {
      setLoadingConnections(false);
    }
  };

  const executeParameterized = async (endpoint) => {
    const value = params[endpoint.key]?.trim();

    if (!value) {
      setConsoleState({
        status: "error",
        title: "Dato requerido",
        detail: `Debes ingresar ${endpoint.inputName} antes de ejecutar este endpoint.`,
        method: endpoint.method,
        path: endpoint.pathTemplate,
        payload: {
          required: endpoint.inputName
        }
      });
      return;
    }

    await executeRequest({
      key: endpoint.key,
      label: endpoint.label,
      method: endpoint.method,
      path: buildPath(endpoint.pathTemplate, endpoint.inputName, value)
    });

    if (endpoint.key === "delete-connection-by-id") {
      loadConnections();
    }
  };

  const handleConnectionField = (field, value) => {
    setConnectionForm((current) => ({
      ...current,
      [field]: value
    }));
  };

  const handleEngineChange = (motor) => {
    const engineConfig = ENGINE_CONFIG[motor];

    setConnectionForm((current) => ({
      ...current,
      motor,
      nombre: current.nombre.includes(current.motor)
        ? current.nombre.replace(current.motor, motor)
        : `${motor} Real`,
      port: engineConfig.port
    }));
  };

  const buildConnectionPayload = () => ({
    nombre: connectionForm.nombre.trim(),
    motor: connectionForm.motor,
    host: connectionForm.host.trim(),
    port: Number(connectionForm.port),
    database_name: connectionForm.database_name.trim(),
    user_name: connectionForm.user_name.trim(),
    password: connectionForm.password
  });

  const validateConnectionForm = () => {
    const payload = buildConnectionPayload();

    if (!payload.nombre || !payload.motor || !payload.host || !payload.database_name || !payload.user_name || !payload.password) {
      setConsoleState({
        status: "error",
        title: "Formulario incompleto",
        detail: "Completa todos los campos antes de ejecutar la prueba.",
        method: "POST",
        path: "/connections",
        payload: {
          required: ["nombre", "motor", "host", "port", "database_name", "user_name", "password"]
        }
      });
      return null;
    }

    if (!Number.isInteger(payload.port) || payload.port <= 0) {
      setConsoleState({
        status: "error",
        title: "Puerto inválido",
        detail: "El puerto debe ser un número mayor que cero.",
        method: "POST",
        path: "/connections",
        payload: {
          port: payload.port
        }
      });
      return null;
    }

    return payload;
  };

  const testConnectionForm = async () => {
    const payload = validateConnectionForm();
    if (!payload) return;

    await executeRequest({
      key: "connection-form-test",
      label: "Probar conexión real",
      method: "POST",
      path: "/connections/test",
      data: payload
    });
  };

  const registerConnectionForm = async () => {
    const payload = validateConnectionForm();
    if (!payload) return;

    const result = await executeRequest({
      key: "connection-form-register",
      label: "Registrar nueva conexión real",
      method: "POST",
      path: "/connections?validate_connection=true",
      data: payload
    });

    if (result) {
      setShowConnectionModal(false);
      await loadConnections();
    }
  };

  const testSavedConnection = async (connectionId) => {
    await executeRequest({
      key: `test-saved-${connectionId}`,
      label: `Probar conexión ${connectionId}`,
      method: "POST",
      path: `/connections/${connectionId}/test`
    });

    loadConnections();
  };

  const deleteSavedConnection = async (connectionId) => {
    const accepted = window.confirm(`¿Seguro que quieres eliminar la conexión ID ${connectionId}?`);
    if (!accepted) return;

    await executeRequest({
      key: `delete-saved-${connectionId}`,
      label: `Eliminar conexión ${connectionId}`,
      method: "DELETE",
      path: `/connections/${connectionId}`
    });

    loadConnections();
  };

  if (!open) return null;

  return (
    <div className="demo-panel-layer" role="presentation">
      <button
        className="demo-panel-backdrop"
        type="button"
        aria-label="Cerrar panel de pruebas"
        onClick={onClose}
      />

      <aside className="demo-panel" aria-label="Panel lateral de pruebas de API">
        <header className="demo-panel-header">
          <div>
            <span className="demo-panel-eyebrow">Entorno visual</span>
            <h2>{panelTitle}</h2>
            <p>Ejecuta endpoints sin salir del dashboard.</p>
          </div>

          <button
            className="demo-panel-close"
            type="button"
            onClick={onClose}
            aria-label="Cerrar panel"
          >
            ×
          </button>
        </header>

        <div className="demo-panel-body">
          <section className="demo-panel-section">
            <h3>Conexiones reales</h3>

            <div className="connection-toolbar">
              <button
                className="connection-primary-button"
                type="button"
                disabled={isRunning}
                onClick={() => setShowConnectionModal(true)}
              >
                Registrar Nueva Conexión
              </button>

              <button
                className="connection-secondary-button"
                type="button"
                disabled={loadingConnections}
                onClick={loadConnections}
              >
                Actualizar lista
              </button>
            </div>

            <div className="connection-list">
              {loadingConnections && <p className="connection-empty">Cargando conexiones...</p>}

              {!loadingConnections && savedConnections.length === 0 && (
                <p className="connection-empty">No hay conexiones registradas todavía.</p>
              )}

              {!loadingConnections && savedConnections.map((connection) => (
                <article className="connection-card" key={connection.id}>
                  <div>
                    <strong>{connection.nombre}</strong>
                    <span>
                      ID {connection.id} · {connection.motor} · {connection.host}:{connection.port}/{connection.database_name}
                    </span>
                    <small>Usuario: {connection.user_name}</small>
                  </div>

                  <div className="connection-actions">
                    <span className={`connection-status connection-status-${String(connection.status || "unknown").toLowerCase()}`}>
                      {connection.status || "UNKNOWN"}
                    </span>

                    <button
                      type="button"
                      disabled={isRunning}
                      onClick={() => testSavedConnection(connection.id)}
                    >
                      Probar
                    </button>

                    <button
                      className="danger"
                      type="button"
                      disabled={isRunning}
                      onClick={() => deleteSavedConnection(connection.id)}
                    >
                      Eliminar
                    </button>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="demo-panel-section">
            <h3>Endpoints directos</h3>

            <div className="demo-endpoint-list">
              {directEndpoints.map((endpoint) => {
                const requestKey = `${endpoint.method}-${endpoint.path}`;

                return (
                  <button
                    key={requestKey}
                    className="demo-endpoint-button"
                    type="button"
                    disabled={isRunning}
                    onClick={() => executeRequest(endpoint)}
                  >
                    <span>{endpoint.label}</span>
                    <small>{endpoint.method}</small>
                  </button>
                );
              })}
            </div>
          </section>

          <section className="demo-panel-section">
            <h3>Endpoints parametrizados</h3>

            <div className="demo-param-list">
              {parameterizedEndpoints.map((endpoint) => (
                <div className="demo-param-row" key={endpoint.key}>
                  <div>
                    <strong>{endpoint.label}</strong>
                    <span>
                      {endpoint.method} {endpoint.pathTemplate}
                    </span>
                  </div>

                  <input
                    value={params[endpoint.key]}
                    placeholder={endpoint.placeholder}
                    onChange={(event) =>
                      setParams((current) => ({
                        ...current,
                        [endpoint.key]: event.target.value
                      }))
                    }
                  />

                  <button
                    type="button"
                    disabled={isRunning}
                    onClick={() => executeParameterized(endpoint)}
                  >
                    Ejecutar
                  </button>
                </div>
              ))}
            </div>
          </section>
        </div>

        <footer className={`demo-console demo-console-${consoleState.status}`}>
          <div className="demo-console-head">
            <div>
              <strong>{consoleState.title}</strong>
              <span>{consoleState.detail}</span>
            </div>

            {consoleState.method && <small>{consoleState.method}</small>}
          </div>

          {consoleState.path && (
            <code className="demo-console-path">{consoleState.path}</code>
          )}

          <pre>{formatPayload(consoleState.payload)}</pre>
        </footer>
      </aside>

      {showConnectionModal && (
        <div className="connection-modal-layer" role="presentation">
          <button
            className="connection-modal-backdrop"
            type="button"
            aria-label="Cerrar formulario de conexión"
            onClick={() => setShowConnectionModal(false)}
          />

          <section className="connection-modal" aria-label="Formulario para registrar nueva conexión">
            <header className="connection-modal-header">
              <div>
                <span>Registro real de motor</span>
                <h3>Registrar Nueva Conexión</h3>
                <p>Primero se prueba la conexión real. Solo se guarda si responde correctamente.</p>
              </div>

              <button
                type="button"
                onClick={() => setShowConnectionModal(false)}
                aria-label="Cerrar modal"
              >
                ×
              </button>
            </header>

            <div className="connection-form-grid">
              <label>
                Tipo de Motor
                <select
                  value={connectionForm.motor}
                  onChange={(event) => handleEngineChange(event.target.value)}
                >
                  {Object.keys(ENGINE_CONFIG).map((motor) => (
                    <option value={motor} key={motor}>{motor}</option>
                  ))}
                </select>
              </label>

              <label>
                Nombre visible
                <input
                  value={connectionForm.nombre}
                  onChange={(event) => handleConnectionField("nombre", event.target.value)}
                  placeholder={`${connectionForm.motor} Producción`}
                />
              </label>

              <label>
                Host
                <input
                  value={connectionForm.host}
                  onChange={(event) => handleConnectionField("host", event.target.value)}
                  placeholder={selectedEngineConfig.hostPlaceholder}
                />
              </label>

              <label>
                Puerto
                <input
                  type="number"
                  value={connectionForm.port}
                  onChange={(event) => handleConnectionField("port", event.target.value)}
                  placeholder={String(selectedEngineConfig.port)}
                />
              </label>

              <label>
                Nombre de BD / Service Name
                <input
                  value={connectionForm.database_name}
                  onChange={(event) => handleConnectionField("database_name", event.target.value)}
                  placeholder={selectedEngineConfig.dbPlaceholder}
                />
              </label>

              <label>
                Usuario
                <input
                  value={connectionForm.user_name}
                  onChange={(event) => handleConnectionField("user_name", event.target.value)}
                  placeholder={selectedEngineConfig.userPlaceholder}
                />
              </label>

              <label className="connection-form-full">
                Contraseña
                <input
                  type="password"
                  value={connectionForm.password}
                  onChange={(event) => handleConnectionField("password", event.target.value)}
                  placeholder="Contraseña real del motor"
                />
              </label>
            </div>

            <div className="connection-modal-note">
              <strong>Tip Docker:</strong> si la BD está instalada en tu Windows y el backend corre en contenedor, usa <code>host.docker.internal</code> como host.
            </div>

            <footer className="connection-modal-actions">
              <button
                type="button"
                className="connection-secondary-button"
                disabled={isRunning}
                onClick={testConnectionForm}
              >
                Probar conexión
              </button>

              <button
                type="button"
                className="connection-primary-button"
                disabled={isRunning}
                onClick={registerConnectionForm}
              >
                Probar y guardar
              </button>
            </footer>
          </section>
        </div>
      )}
    </div>
  );
}

export default DemoPanel;
