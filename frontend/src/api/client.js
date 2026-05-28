import axios from "axios";

export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  timeout: 12000
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export async function loginRequest(username, password) {
  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);

  const response = await api.post("/token", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded"
    }
  });

  return response.data;
}

export const dashboardApi = {
  healthSummary: () => api.get("/health-summary"),
  performance: () => api.get("/bi/performance"),
  slowQueries: () => api.get("/bi/top-slow-queries"),
  backupSla: () => api.get("/bi/backup-sla"),
  availability: () => api.get("/bi/availability"),
  replicationLag: () => api.get("/bi/replication-lag"),
  replicationStatus: () => api.get("/replication/status"),
  backupHistory: () => api.get("/backup/history"),
  backupSnapshots: () => api.get("/backup/snapshots"),
  cacheSummary: () => api.get("/cache/summary"),
  alertLogs: () => api.get("/alerts/logs"),
  resolveAllAlerts: () => api.put("/alerts/resolve-all"),
  jobAudit: () => api.get("/jobs/audit")
};
