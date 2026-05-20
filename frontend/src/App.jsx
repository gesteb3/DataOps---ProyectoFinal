import { useEffect, useState } from "react";
import axios from "axios";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar
} from "recharts";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [health, setHealth] = useState(null);
  const [backupSla, setBackupSla] = useState(null);
  const [cacheSummary, setCacheSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [performance, setPerformance] = useState([]);
  const [slowQueries, setSlowQueries] = useState([]);
  const [replication, setReplication] = useState([]);

  const authHeaders = {
    headers: {
      Authorization: `Bearer ${token}`
    }
  };

  const login = async (e) => {
    e.preventDefault();
    setError("");

    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const response = await axios.post(`${API_URL}/token`, formData, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded"
        }
      });

      localStorage.setItem("token", response.data.access_token);
      setToken(response.data.access_token);
    } catch {
      setError("Credenciales inválidas o API no disponible");
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken("");
  };

  const loadDashboard = async () => {
    setLoading(true);
    setError("");

    try {
      const [
        healthRes,
        backupRes,
        cacheRes,
        alertsRes,
        performanceRes,
        slowQueriesRes,
        replicationRes
      ] = await Promise.all([
        axios.get(`${API_URL}/health-summary`, authHeaders),
        axios.get(`${API_URL}/bi/backup-sla`, authHeaders),
        axios.get(`${API_URL}/cache/summary`, authHeaders),
        axios.get(`${API_URL}/alerts/logs`, authHeaders),
        axios.get(`${API_URL}/bi/performance`, authHeaders),
        axios.get(`${API_URL}/bi/top-slow-queries`, authHeaders),
        axios.get(`${API_URL}/replication/status`, authHeaders)
      ]);

      setHealth(healthRes.data);
      setBackupSla(backupRes.data);
      setCacheSummary(cacheRes.data);
      setAlerts(alertsRes.data);
      setPerformance(performanceRes.data.slice(0, 20).reverse());
      setSlowQueries(slowQueriesRes.data);
      setReplication(replicationRes.data.slice(-10));
    } catch {
      setError("No se pudieron cargar los datos. Revisa el token o el backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      loadDashboard();
    }
  }, [token]);

  if (!token) {
    return (
      <main className="login-page">
        <form className="login-card" onSubmit={login}>
          <h1>DataOps Control Center</h1>

          <label>Usuario</label>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />

          <label>Contraseña</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          {error && <div className="error">{error}</div>}

          <button type="submit">Ingresar</button>
        </form>
      </main>
    );
  }

  return (
    <main className="dashboard">
      <header className="header">
        <div>
          <h1>DataOps Control Center</h1>
          <p>Dashboard operativo con métricas, backups, caché y alertas</p>
        </div>

        <div className="header-actions">
          <button onClick={loadDashboard}>
            {loading ? "Cargando..." : "Actualizar"}
          </button>
          <button className="secondary" onClick={logout}>
            Cerrar sesión
          </button>
        </div>
      </header>

      {error && <div className="error">{error}</div>}

      <section className="cards">
        <div className="card">
          <span>Motores registrados</span>
          <strong>{health?.registered_engines ?? 0}</strong>
        </div>

        <div className="card">
          <span>CPU actual</span>
          <strong>{health?.latest_cpu ?? 0}%</strong>
        </div>

        <div className="card">
          <span>SLA Backups</span>
          <strong>{backupSla?.sla_compliance ?? "No"}</strong>
        </div>

        <div className="card">
          <span>Cache Hit Rate</span>
          <strong>{cacheSummary?.hit_rate_percentage ?? 0}%</strong>
        </div>

        <div className="card">
          <span>Alertas registradas</span>
          <strong>{alerts?.length ?? 0}</strong>
        </div>
      </section>

      <section className="grid">
        <div className="panel">
          <h2>Rendimiento temporal</h2>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={performance}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="capture_time" hide />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="cpu" name="CPU" />
              <Line type="monotone" dataKey="connections" name="Conexiones" />
              <Line type="monotone" dataKey="locks" name="Locks" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="panel">
          <h2>Lag de replicación</h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={replication}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="scenario" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="replication_lag" name="Lag segundos" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="grid">
        <div className="panel">
          <h2>Top queries lentas</h2>
          <table>
            <thead>
              <tr>
                <th>Query</th>
                <th>Promedio ms</th>
                <th>Ejecuciones</th>
              </tr>
            </thead>
            <tbody>
              {slowQueries.map((query, index) => (
                <tr key={index}>
                  <td>{query.query_text}</td>
                  <td>{query.average_duration_ms}</td>
                  <td>{query.executions}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="panel">
          <h2>Alertas recientes</h2>
          <table>
            <thead>
              <tr>
                <th>Condición</th>
                <th>Severidad</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {alerts.slice(0, 8).map((alert) => (
                <tr key={alert.id}>
                  <td>{alert.condition_triggered}</td>
                  <td>{alert.severity}</td>
                  <td>{alert.resolution_status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h2>Estado de backups y SLA</h2>
        <div className="backup-info">
          <p><b>RPO objetivo:</b> {backupSla?.rpo_target_minutes ?? 15} minutos</p>
          <p><b>RTO objetivo:</b> {backupSla?.rto_target_minutes ?? 45} minutos</p>
          <p><b>RPO actual:</b> {backupSla?.actual_rpo_minutes ?? 0} minutos</p>
          <p><b>RTO proyectado:</b> {backupSla?.projected_rto_minutes ?? 0} minutos</p>
          <p><b>Último backup:</b> {backupSla?.latest_backup?.file_name ?? "Sin datos"}</p>
        </div>
      </section>
    </main>
  );
}

export default App;