import { useEffect, useMemo, useState } from "react";
import { api, API_URL } from "../api/client";

const directEndpoints = [
  { label: "Simular concurrencia", method: "POST", path: "/concurrency/simulate" },
  { label: "Deadlock real PostgreSQL", method: "POST", path: "/concurrency/real-deadlock-postgres" },
  { label: "Simular desastre", method: "POST", path: "/backup/simulate-disaster" },
  { label: "Restaurar backup", method: "POST", path: "/backup/restore" },
  { label: "Evaluar alertas", method: "POST", path: "/alerts/evaluate" },
  { label: "Simular replicación", method: "POST", path: "/replication/simulate" },
  { label: "Probar conexiones", method: "POST", path: "/connections/test" },
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
    label: "Probar conexión por ID",
    method: "POST",
    pathTemplate: "/connections/{connection_id}/test",
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
  const [params, setParams] = useState({
    "invalidate-cache": "",
    "test-connection-by-id": "",
    "get-cache-query": ""
  });

  const isRunning = Boolean(runningKey);

  const panelTitle = useMemo(() => {
    if (isRunning) return "Ejecutando prueba...";
    return "Demo/Pruebas API";
  }, [isRunning]);

  useEffect(() => {
    if (!open) return undefined;

    const handleEscape = (event) => {
      if (event.key === "Escape") onClose();
    };

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [open, onClose]);

  const executeRequest = async ({ key, label, method, path }) => {
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
      const response = await api.request({ method, url: path });
      const duration = Math.round(performance.now() - startedAt);

      setConsoleState({
        status: "success",
        title: "Ejecución exitosa",
        detail: `HTTP ${response.status} · ${duration} ms`,
        method,
        path,
        payload: response.data
      });

      if (typeof onAfterRun === "function") {
        onAfterRun();
      }
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
    } finally {
      setRunningKey("");
    }
  };

  const executeParameterized = (endpoint) => {
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

    executeRequest({
      key: endpoint.key,
      label: endpoint.label,
      method: endpoint.method,
      path: buildPath(endpoint.pathTemplate, endpoint.inputName, value)
    });
  };

  if (!open) return null;

  return (
    <div className="demo-panel-layer" role="presentation">
      <button className="demo-panel-backdrop" type="button" aria-label="Cerrar panel de pruebas" onClick={onClose} />

      <aside className="demo-panel" aria-label="Panel lateral de pruebas de API">
        <header className="demo-panel-header">
          <div>
            <span className="demo-panel-eyebrow">Entorno visual</span>
            <h2>{panelTitle}</h2>
            <p>Ejecuta endpoints sin salir del dashboard.</p>
          </div>
          <button className="demo-panel-close" type="button" onClick={onClose} aria-label="Cerrar panel">
            ×
          </button>
        </header>

        <div className="demo-panel-body">
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
                    <span>{endpoint.method} {endpoint.pathTemplate}</span>
                  </div>

                  <input
                    value={params[endpoint.key]}
                    placeholder={endpoint.placeholder}
                    onChange={(event) => setParams((current) => ({ ...current, [endpoint.key]: event.target.value }))}
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

          {consoleState.path && <code className="demo-console-path">{consoleState.path}</code>}

          <pre>{formatPayload(consoleState.payload)}</pre>
        </footer>
      </aside>
    </div>
  );
}

export default DemoPanel;
