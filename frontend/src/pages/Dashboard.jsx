import { useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { dashboardApi } from "../api/client";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import StatCard from "../components/StatCard";
import ChartCard from "../components/ChartCard";
import DataTable from "../components/DataTable";

const initialData = {
  health: null,
  performance: [],
  slowQueries: [],
  backupSla: null,
  availability: [],
  replicationLag: [],
  replicationStatus: [],
  backupHistory: [],
  backupSnapshots: [],
  cacheSummary: null,
  alertLogs: [],
  jobAudit: []
};

const AUTO_REFRESH_MS = 10000;
const endpointConfig = [
  ["health", dashboardApi.healthSummary],
  ["performance", dashboardApi.performance],
  ["slowQueries", dashboardApi.slowQueries],
  ["backupSla", dashboardApi.backupSla],
  ["availability", dashboardApi.availability],
  ["replicationLag", dashboardApi.replicationLag],
  ["replicationStatus", dashboardApi.replicationStatus],
  ["backupHistory", dashboardApi.backupHistory],
  ["backupSnapshots", dashboardApi.backupSnapshots],
  ["cacheSummary", dashboardApi.cacheSummary],
  ["alertLogs", dashboardApi.alertLogs],
  ["jobAudit", dashboardApi.jobAudit]
];

function formatDate(value) {
  if (!value) return "—";

  try {
    return new Intl.DateTimeFormat("es-GT", {
      dateStyle: "short",
      timeStyle: "short"
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function getErrorMessage(error) {
  const status = error?.response?.status;

  if (status === 401) return "Token inválido o sesión expirada.";
  if (status === 404) return "Endpoint no encontrado en el backend.";
  if (status >= 500) return "Error interno del backend.";

  return "No se pudo cargar esta sección.";
}

function statusBadge(status) {
  const normalized = String(status || "SIN ESTADO").toUpperCase();
  const isOk = ["OK", "ONLINE", "SUCCESS", "EXITOSO", "RESOLVED"].some((word) => normalized.includes(word));
  const isBad = ["CRITICAL", "FAILED", "ERROR", "PENDING", "CRÍTICO"].some((word) => normalized.includes(word));

  return <span className={`badge ${isBad ? "danger" : isOk ? "success" : "warning"}`}>{status || "—"}</span>;
}

const officialEngines = ["PostgreSQL", "SQL Server", "Oracle"];

function normalizeEngineName(value = "") {
  const text = String(value).toLowerCase();

  if (text.includes("postgres")) return "PostgreSQL";
  if (text.includes("sql server") || text.includes("sqlserver") || text.includes("mssql")) return "SQL Server";
  if (text.includes("oracle")) return "Oracle";

  return null;
}

function getAverageAvailabilityByEngine(items = []) {
  const grouped = new Map();

  items.forEach((item) => {
    const rawName =
      item.motor ||
      item.engine_type ||
      item.database_type ||
      item.engine ||
      item.nombre ||
      item.name ||
      "";

    const engineName = normalizeEngineName(rawName);
    if (!engineName) return;

    const value = Number(item.availability_percentage ?? item.availability ?? 0);
    const target = Number(item.target_percentage ?? 99.9);

    if (!grouped.has(engineName)) {
      grouped.set(engineName, {
        engine: engineName,
        total: 0,
        count: 0,
        target_percentage: target
      });
    }

    const current = grouped.get(engineName);
    current.total += value;
    current.count += 1;
  });

  return officialEngines
    .map((engine) => {
      const item = grouped.get(engine);
      if (!item) return null;

      return {
        engine: item.engine,
        availability_percentage: Number((item.total / item.count).toFixed(2)),
        target_percentage: item.target_percentage
      };
    })
    .filter(Boolean);
}
function Dashboard({ onLogout }) {
  const [data, setData] = useState(initialData);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(true);
  const [actionMessage, setActionMessage] = useState("");

  const loadDashboard = async ({ silent = false } = {}) => {
    if (!silent) {
      setLoading(true);
      setActionMessage("");
    }

    const results = await Promise.allSettled(
      endpointConfig.map(([, request]) => request())
    );

    const nextData = { ...initialData };
    const nextErrors = {};

    results.forEach((result, index) => {
      const [key] = endpointConfig[index];

      if (result.status === "fulfilled") {
        nextData[key] = result.value.data;
      } else {
        nextData[key] = initialData[key];
        nextErrors[key] = getErrorMessage(result.reason);
      }
    });

    setData(nextData);
    setErrors(nextErrors);
    setLoading(false);
  };

  const handleResolveAllAlerts = async () => {
    setActionMessage("");

    try {
      const response = await dashboardApi.resolveAllAlerts();
      setActionMessage(`Alertas resueltas: ${response.data.alerts_resolved ?? 0}`);
      await loadDashboard();
    } catch {
      setActionMessage("No se pudieron resolver las alertas pendientes.");
    }
  };

  useEffect(() => {
    loadDashboard();

    const intervalId = window.setInterval(() => {
      loadDashboard({ silent: true });
    }, AUTO_REFRESH_MS);

    return () => window.clearInterval(intervalId);
  }, []);

  const performance = useMemo(
    () => [...(data.performance || [])].reverse().slice(-25),
    [data.performance]
  );

  const availability = useMemo(
    () => getAverageAvailabilityByEngine(data.availability || []),
    [data.availability]
  );
  const replicationLag = useMemo(
    () => [...(data.replicationLag || [])].reverse().slice(-12),
    [data.replicationLag]
  );

  const pendingAlerts = useMemo(
    () => (data.alertLogs || []).filter((alert) => alert.resolution_status === "PENDING"),
    [data.alertLogs]
  );

  const criticalAlerts = pendingAlerts.filter((alert) => String(alert.severity).toLowerCase().includes("critical"));
  const latestMetric = performance[performance.length - 1] || {};
  const hasMemory = performance.some((item) => item.memory !== undefined && item.memory !== null);

  const cacheHitRate = data.cacheSummary?.hit_rate_percentage ?? data.cacheSummary?.hit_rate ?? 0;
  const cacheHits = data.cacheSummary?.cache_hits ?? data.cacheSummary?.hits ?? 0;
  const cacheMisses = data.cacheSummary?.cache_misses ?? data.cacheSummary?.misses ?? 0;
  const latestLag = replicationLag[replicationLag.length - 1]?.replication_lag ?? 0;

  return (
    <div className="app-shell">
      <Sidebar />

      <main className="content">
        <Header
          loading={loading}
          onRefresh={loadDashboard}
          onLogout={onLogout}
          onResolveAll={handleResolveAllAlerts}
          pendingAlerts={pendingAlerts.length}
        />

        {actionMessage && <div className="action-message">{actionMessage}</div>}

        {criticalAlerts.length > 0 && (
          <section className="critical-banner" id="critical-alerts">
            <div>
              <span>Atención requerida</span>
              <strong>{criticalAlerts.length} alerta(s) crítica(s) pendientes</strong>
              <p>Revisa las condiciones generadas automáticamente por CPU, disco, deadlocks, backups o replicación.</p>
            </div>
            <button className="btn btn-light" onClick={handleResolveAllAlerts}>Resolver ahora</button>
          </section>
        )}

        <section className="stats-grid" id="overview">
          <StatCard title="Motores registrados" value={data.health?.registered_engines ?? 0} subtitle="Conexiones configuradas" icon="DB" />
          <StatCard title="Métricas capturadas" value={data.health?.captured_metrics ?? 0} subtitle={data.health?.status ?? "Sin estado"} tone="purple" icon="M" />
          <StatCard title="CPU actual" value={`${data.health?.latest_cpu ?? latestMetric.cpu ?? 0}%`} subtitle="Última métrica registrada" tone="orange" icon="CPU" />
          <StatCard title="Disco actual" value={`${data.health?.latest_disk_usage ?? latestMetric.disk_usage ?? 0}%`} subtitle="Uso de almacenamiento" tone="green" icon="HD" />
          <StatCard title="SLA Backups" value={data.backupSla?.sla_compliance ?? "No"} subtitle={`RPO ${data.backupSla?.rpo_target_minutes ?? 15} min / RTO ${data.backupSla?.rto_target_minutes ?? 45} min`} tone="blue" icon="SLA" />
          <StatCard title="Cache Hit Rate" value={`${cacheHitRate}%`} subtitle={`${cacheHits} hits / ${cacheMisses} misses`} tone="green" icon="R" />
          <StatCard title="Alertas pendientes" value={pendingAlerts.length} subtitle={`${criticalAlerts.length} críticas`} tone={pendingAlerts.length ? "red" : "green"} icon="!" />
          <StatCard title="Último lag" value={`${latestLag} s`} subtitle="Replicación" tone="purple" icon="↔" />
        </section>

        <section className="dashboard-grid two" id="performance">
          <ChartCard title="Rendimiento temporal" subtitle="" error={errors.performance} loading={loading}>
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={performance} margin={{ top: 10, right: 18, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="capture_time" tickFormatter={formatDate} minTickGap={28} />
                <YAxis />
                <Tooltip labelFormatter={formatDate} />
                <Legend />
                <Line type="monotone" dataKey="cpu" name="CPU" stroke="#f97316" strokeWidth={3} dot={false} />
                {hasMemory && <Line type="monotone" dataKey="memory" name="Memoria" stroke="#8b5cf6" strokeWidth={3} dot={false} />}
                <Line type="monotone" dataKey="disk_usage" name="Disco" stroke="#22c55e" strokeWidth={3} dot={false} />
                <Line type="monotone" dataKey="connections" name="Conexiones" stroke="#2563eb" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Disponibilidad por motor" subtitle="Comparación contra objetivo SLA 99.9%" error={errors.availability} loading={loading}>
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={availability} margin={{ top: 10, right: 18, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="engine" minTickGap={18} />
                <YAxis domain={[98, 100]} />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="availability_percentage" name="Disponibilidad" strokeWidth={3} fillOpacity={0.2} />
                <Line type="monotone" dataKey="target_percentage" name="Objetivo" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>
        </section>

        <section className="dashboard-grid two" id="replication">
          <ChartCard title="Lag de replicación" subtitle="Últimos escenarios registrados" error={errors.replicationLag} loading={loading}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={replicationLag} margin={{ top: 10, right: 18, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="scenario" minTickGap={18} />
                <YAxis />
                <Tooltip labelFormatter={(value) => `Escenario: ${value}`} />
                <Bar dataKey="replication_lag" name="Lag en segundos" radius={[10, 10, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Top queries lentas" subtitle="+" error={errors.slowQueries} loading={loading}>
            <DataTable
              compact
              rows={(data.slowQueries || []).slice(0, 10)}
              columns={[
                { key: "query_text", label: "Consulta", render: (row) => <span className="query-text">{row.query_text}</span> },
                { key: "average_duration_ms", label: "Prom. ms" },
                { key: "max_duration_ms", label: "Máx. ms" },
                { key: "executions", label: "Ejec." }
              ]}
            />
          </ChartCard>
        </section>

        <section className="dashboard-grid two" id="alerts">
          <ChartCard title="Alertas registradas" subtitle="" error={errors.alertLogs} loading={loading}>
            <DataTable
              rows={(data.alertLogs || []).slice(0, 10)}
              columns={[
                { key: "condition_triggered", label: "Condición" },
                { key: "affected_engine", label: "Motor" },
                { key: "severity", label: "Severidad", render: (row) => statusBadge(row.severity) },
                { key: "resolution_status", label: "Estado", render: (row) => statusBadge(row.resolution_status) },
                { key: "created_at", label: "Fecha", render: (row) => formatDate(row.created_at) }
              ]}
            />
          </ChartCard>

          <ChartCard title="Estado de replicación" subtitle="Últimos estados" error={errors.replicationStatus} loading={loading}>
            <DataTable
              rows={(data.replicationStatus || []).slice(-10).reverse()}
              columns={[
                { key: "scenario", label: "Escenario" },
                { key: "replication_lag", label: "Lag", render: (row) => `${row.replication_lag ?? 0} s` },
                { key: "status", label: "Estado", render: (row) => statusBadge(row.status) },
                { key: "created_at", label: "Fecha", render: (row) => formatDate(row.created_at) }
              ]}
            />
          </ChartCard>
        </section>

        <section className="chart-card" id="backups">
          <div className="section-heading">
            <div>
              <h2>Backups y cumplimiento SLA</h2>
              <p>Historial de backups, snapshots y objetivos RPO/RTO.</p>
            </div>
            {statusBadge(data.backupSla?.sla_compliance === "Sí" ? "SLA OK" : "SLA NO")}
          </div>

          <div className="sla-grid">
            <div><span>RPO objetivo</span><strong>{data.backupSla?.rpo_target_minutes ?? 15} min</strong></div>
            <div><span>RTO objetivo</span><strong>{data.backupSla?.rto_target_minutes ?? 45} min</strong></div>
            <div><span>RPO actual</span><strong>{data.backupSla?.actual_rpo_minutes ?? 0} min</strong></div>
            <div><span>RTO proyectado</span><strong>{data.backupSla?.projected_rto_minutes ?? 0} min</strong></div>
            <div><span>Último backup</span><strong>{data.backupSla?.latest_backup?.file_name ?? "Sin datos"}</strong></div>
          </div>

          <div className="dashboard-grid two inner-grid">
            <DataTable
              rows={(data.backupHistory || []).slice(0, 8)}
              emptyMessage={errors.backupHistory || "Sin backups registrados"}
              columns={[
                { key: "backup_type", label: "Tipo" },
                { key: "file_name", label: "Archivo" },
                { key: "size_mb", label: "MB" },
                { key: "duration_seconds", label: "Seg." },
                { key: "created_at", label: "Fecha", render: (row) => formatDate(row.created_at) }
              ]}
            />

            <DataTable
              rows={(data.backupSnapshots || []).slice(0, 8)}
              emptyMessage={errors.backupSnapshots || "Sin snapshots registrados"}
              columns={[
                { key: "snapshot_name", label: "Snapshot" },
                { key: "backup_type", label: "Tipo" },
                { key: "file_name", label: "Archivo" },
                { key: "created_at", label: "Fecha", render: (row) => formatDate(row.created_at) }
              ]}
            />
          </div>
        </section>

        <section className="chart-card" id="audit">
          <div className="section-heading">
            <div>
              <h2>Auditoría de jobs automáticos</h2>
              <p>Procesos registrados </p>
            </div>
            <span className="pill">{(data.jobAudit || []).length} registros</span>
          </div>

          {errors.jobAudit ? (
            <div className="section-error">{errors.jobAudit}</div>
          ) : (
            <DataTable
              rows={(data.jobAudit || []).slice(0, 12)}
              columns={[
                { key: "job_name", label: "Job" },
                { key: "status", label: "Estado", render: (row) => statusBadge(row.status) },
                { key: "records_processed", label: "Registros" },
                { key: "start_time", label: "Inicio", render: (row) => formatDate(row.start_time) },
                { key: "end_time", label: "Fin", render: (row) => formatDate(row.end_time) },
                { key: "error_message", label: "Error" }
              ]}
            />
          )}
        </section>
      </main>
    </div>
  );
}

export default Dashboard;
