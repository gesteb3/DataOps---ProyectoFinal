import { useState } from "react";
import { loginRequest } from "../api/client";

function Login({ onLogin }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const data = await loginRequest(username, password);
      localStorage.setItem("token", data.access_token);
      onLogin(data.access_token);
    } catch {
      setError("Credenciales inválidas o backend no disponible.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login-layout">
      <section className="login-hero">
        <span className="eyebrow">DataOps Control Center</span>
        <h1>Panel de monitoreo</h1>
      </section>

      <form className="login-card" onSubmit={handleSubmit}>
        <div className="login-logo">D</div>
        <h2>Iniciar sesión</h2>
        <p>Usa las credenciales de prueba del proyecto.</p>

        <label htmlFor="username">Usuario</label>
        <input
          id="username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          autoComplete="username"
        />

        <label htmlFor="password">Contraseña</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
        />

        {error && <div className="section-error">{error}</div>}

        <button className="btn btn-primary full" type="submit" disabled={loading}>
          {loading ? "Validando..." : "Entrar al dashboard"}
        </button>
      </form>
    </main>
  );
}

export default Login;
