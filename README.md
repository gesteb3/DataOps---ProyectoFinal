# DataOps Control Center

DataOps Control Center es una plataforma para monitoreo, respaldo, análisis, caché, replicación y alertas de motores de bases de datos. El proyecto integra FastAPI, PostgreSQL, Redis, AWS S3, autenticación JWT, frontend React con Vite y visualización analítica en Power BI.

## Objetivo

Centralizar operaciones de administración de bases de datos mediante una plataforma que permite registrar motores, capturar métricas, analizar consultas lentas, simular concurrencia, gestionar backups, replicar información hacia la nube, usar caché con Redis, generar alertas y visualizar indicadores desde un dashboard web y Power BI.

## Stack tecnológico

Backend:

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- APScheduler
- JWT
- Swagger/OpenAPI
- psycopg2
- pyodbc
- oracledb
- Boto3
- Redis

Frontend:

- React
- Vite
- Axios
- Recharts
- CSS responsivo

Infraestructura:

- Docker
- Docker Compose
- PostgreSQL en contenedor
- Redis en contenedor
- AWS S3 para backups remotos
- Variables de entorno mediante `.env`
- ODBC Driver 18 para SQL Server

Business Intelligence:

- Power BI Desktop
- Endpoints REST protegidos con JWT

## Estructura del proyecto

```txt
DataOps-Control-Center/
├── backend/
│   ├── app/
│   │   ├── modules/
│   │   │   ├── alerts.py
│   │   │   ├── backup.py
│   │   │   ├── bi.py
│   │   │   ├── cache.py
│   │   │   ├── concurrency.py
│   │   │   └── replication.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── db_connectors.py
│   │   ├── database.py
│   │   ├── jwt_security.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── scheduler.py
│   │   ├── schemas.py
│   │   └── security.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.js
│   │   ├── components/
│   │   │   ├── Sidebar.jsx
│   │   │   ├── Header.jsx
│   │   │   ├── StatCard.jsx
│   │   │   ├── ChartCard.jsx
│   │   │   └── DataTable.jsx
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   └── Dashboard.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   └── package-lock.json
├── docker-compose.yml
├── .env
├── .gitignore
├── Proyecto Final BDII.pbix
└── README.md
```

## Variables de entorno

El proyecto utiliza un archivo `.env` en la raíz para manejar configuración y credenciales.

Ejemplo:

```env
CLOUD_PROVIDER=AWS
CLOUD_BUCKET=dataops-backups
BACKUP_RETENTION_DAYS=7

AWS_ACCESS_KEY_ID=TU_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=TU_SECRET_KEY
AWS_REGION=us-east-2
AWS_BUCKET=tu-bucket-s3

JWT_SECRET_KEY=CAMBIAR_EN_PRODUCCION
PASSWORD_SECRET=CAMBIAR_EN_PRODUCCION

ALERT_EMAIL_ENABLED=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=correo_origen@gmail.com
SMTP_PASSWORD=app_password
ALERT_EMAIL_TO=correo_destino@gmail.com

CACHE_TTL_SECONDS=60
```

El archivo `.env` no debe subirse al repositorio.

## Variables de entorno del frontend

El frontend puede usar una variable opcional para definir la URL del backend:

```env
VITE_API_URL=http://localhost:8000
```

Si no existe, el frontend usa por defecto:

```txt
http://localhost:8000
```

Esta configuración está centralizada en:

```txt
frontend/src/api/client.js
```

## Instalación y ejecución

### Levantar backend, PostgreSQL y Redis con Docker

Desde la raíz del proyecto:

```cmd
docker compose up --build
```

Servicios principales:

```txt
API FastAPI: http://localhost:8000
Swagger/OpenAPI: http://localhost:8000/docs
PostgreSQL: localhost:5432
Redis: localhost:6379
```

### Levantar frontend

En otra terminal:

```cmd
cd frontend
npm install
npm run dev
```

Frontend disponible en:

```txt
http://localhost:5173
```

Credenciales de prueba:

```txt
Usuario: admin
Contraseña: admin123
```

## Autenticación

El sistema usa autenticación JWT.

Flujo:

1. El usuario inicia sesión mediante `POST /token`.
2. El backend genera un token JWT.
3. El frontend guarda el token en `localStorage`.
4. Las peticiones protegidas usan el encabezado:

```txt
Authorization: Bearer TOKEN
```

Endpoints públicos:

```txt
GET /
GET /health
GET /db-test
POST /login
POST /token
```

Rutas protegidas principales:

```txt
/connections
/metrics
/queries
/backup
/concurrency
/replication
/cache
/bi
/alerts
/jobs
```

## Módulos principales

### Módulo 1: Registro de motores

Permite registrar motores de bases de datos.

Motores soportados:

```txt
PostgreSQL
SQL Server
Oracle
```

Endpoints principales:

```txt
POST /connections
GET /connections
POST /connections/test
POST /connections/{connection_id}/test
POST /connections?validate_connection=true
```

La validación de conectividad se realiza mediante:

```txt
PostgreSQL: psycopg2
SQL Server: pyodbc
Oracle: oracledb
```

### Módulo 2: Health Check automático

Captura métricas periódicas de los motores registrados.

Métricas:

```txt
CPU
Memoria
Conexiones activas
Locks
Deadlocks
Uso de disco
```

Endpoints:

```txt
GET /metrics
GET /health-summary
```

### Módulo 3: Slow Query Monitor

Registra y clasifica consultas según su duración.

Clasificación:

```txt
Fast: menor a 100 ms
Medium: entre 100 ms y 500 ms
Slow: entre 500 ms y 2000 ms
Critical: mayor a 2000 ms
```

Endpoints:

```txt
POST /queries
GET /queries
GET /bi/top-slow-queries
```

### Módulo 4: Concurrencia y Deadlocks

Simula concurrencia con usuarios ejecutando operaciones mixtas.

Operaciones:

```txt
INSERT
UPDATE
DELETE
SELECT
```

Tipos de bloqueo:

```txt
SHARED
EXCLUSIVE
DEADLOCK
TIMEOUT
```

Endpoints:

```txt
POST /concurrency/simulate
POST /concurrency/simulate?force_deadlock=true
POST /concurrency/simulate?force_timeout=true
POST /concurrency/real-deadlock-postgres
GET /concurrency/summary
GET /concurrency/logs
```

### Módulo 5: Backup, Recovery y Nube

Gestiona backups, snapshots, restauración y replicación hacia AWS S3.

Tipos de backup:

```txt
FULL
DIFF
INC
```

Snapshots:

```txt
PRE_DEPLOY
PRE_TEST
PRE_IMPORT
```

Endpoints:

```txt
POST /backup/full
POST /backup/diff
POST /backup/inc
POST /backup/snapshot/{snapshot_name}
POST /backup/simulate-disaster
POST /backup/restore
GET /backup/history
GET /backup/snapshots
GET /backup/retention-policy
GET /bi/backup-sla
```

Cada backup genera un hash SHA256 para verificar integridad del archivo.

### Módulo 6: Replicación distribuida

Simula una arquitectura primario-réplica con medición de lag.

Escenarios:

| Escenario | Lag | Estado |
|---|---:|---|
| Carga normal | 2 segundos | Aceptable |
| Carga media | 5 segundos | Advertencia |
| Carga alta | 20 segundos | Crítico |

Endpoints:

```txt
POST /replication/simulate
GET /replication/status
GET /bi/replication-lag
```

### Módulo 7: Caché con Redis

Implementa Redis como capa de caché para consultas frecuentes.

Comportamientos:

```txt
Cache HIT
Cache MISS
TTL
Invalidación manual
```

Endpoints:

```txt
GET /cache/query/{query_key}
DELETE /cache/invalidate/{query_key}
GET /cache/metrics
GET /cache/summary
```

### Módulo 8: Business Intelligence

Expone endpoints preparados para Power BI y el dashboard React.

Endpoints BI:

```txt
GET /bi/performance
GET /bi/heatmap
GET /bi/top-slow-queries
GET /bi/backup-sla
GET /bi/availability
GET /bi/replication-lag
GET /alerts/logs
```

### Módulo 9: Motor de alertas

Genera alertas automáticas según reglas configurables.

Reglas principales:

```txt
CPU > 85%
Deadlocks > 3
Backup fallido
Lag de replicación > 10 segundos
Disco > 90%
Conexiones > umbral
```

Endpoints:

```txt
POST /alerts/init-rules
GET /alerts/rules
PUT /alerts/rules/{rule_id}
POST /alerts/evaluate
GET /alerts/logs
PUT /alerts/resolve/{alert_id}
PUT /alerts/resolve-all
```

### Auditoría de procesos automáticos

Registra la ejecución de jobs automáticos del sistema.

Endpoint:

```txt
GET /jobs/audit
```

## Frontend React

El frontend está construido con React y Vite.

Características principales:

```txt
Login con JWT
Dashboard administrativo
Sidebar lateral
Header superior
Cards de resumen
Gráficas con Recharts
Tablas administrativas
Botón de actualización manual
Actualización automática
Botón para cerrar sesión
Botón para resolver alertas
Manejo de errores por sección
```

Endpoints consumidos por el dashboard:

```txt
GET /health-summary
GET /bi/performance
GET /bi/top-slow-queries
GET /bi/backup-sla
GET /bi/availability
GET /bi/replication-lag
GET /replication/status
GET /backup/history
GET /backup/snapshots
GET /cache/summary
GET /alerts/logs
PUT /alerts/resolve-all
GET /jobs/audit
```

## Power BI

Power BI consume endpoints protegidos mediante JWT.

Ejemplo:

```txt
URL: http://localhost:8000/bi/performance
Header: Authorization
Valor: Bearer TOKEN
```

Endpoints usados:

```txt
http://localhost:8000/bi/performance
http://localhost:8000/bi/heatmap
http://localhost:8000/bi/top-slow-queries
http://localhost:8000/bi/backup-sla
http://localhost:8000/bi/availability
http://localhost:8000/alerts/logs
```

## Comandos útiles

Levantar servicios:

```cmd
docker compose up --build
```

Detener servicios:

```cmd
docker compose down
```

Reconstruir servicios:

```cmd
docker compose down
docker compose up --build
```

Entrar a PostgreSQL:

```cmd
docker exec -it dataops_postgres psql -U dataops -d dataops_db
```

Ver contenedores activos:

```cmd
docker ps
```

Levantar frontend:

```cmd
cd frontend
npm install
npm run dev
```

Ejecutar frontend usando variable de entorno:

```cmd
cd frontend
set VITE_API_URL=http://localhost:8000
npm run dev
```

## Seguridad

No se deben subir al repositorio:

```txt
.env
Credenciales AWS
Passwords SMTP
Tokens JWT
node_modules
Archivos de entorno reales
```

El backend protege las rutas principales mediante JWT.

El frontend conserva el token en `localStorage` y lo envía automáticamente en las peticiones protegidas.

Las credenciales de conexión de motores no deben almacenarse en texto plano.
