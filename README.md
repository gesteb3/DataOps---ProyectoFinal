# DataOps Control Center

DataOps Control Center es una plataforma de monitoreo, respaldo, análisis y alertas para motores de bases de datos. El proyecto integra backend con FastAPI, base de datos PostgreSQL, Redis para caché, AWS S3 para replicación de backups, autenticación JWT, frontend React y dashboard analítico en Power BI.

## Objetivo del proyecto

El objetivo principal es centralizar operaciones críticas de administración de bases de datos, incluyendo monitoreo de salud, análisis de consultas lentas, concurrencia, backups, replicación, caché, visualización ejecutiva y alertas automáticas.

La plataforma permite registrar motores de base de datos, capturar métricas periódicas, analizar rendimiento, ejecutar simulaciones controladas, generar backups, replicarlos a la nube y visualizar el estado operativo desde un dashboard web y Power BI.

## Stack tecnológico

Backend:

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- APScheduler
- JWT
- Swagger/OpenAPI

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

Business Intelligence:

- Power BI Desktop
- Endpoints REST protegidos con JWT

## Estructura general del proyecto

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
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── package-lock.json
├── docker-compose.yml
├── .env
├── .gitignore
└── README.md
```

## Variables de entorno

El proyecto utiliza un archivo `.env` en la raíz para manejar credenciales y configuración sensible.

Ejemplo:

```env
CLOUD_PROVIDER=AWS
CLOUD_BUCKET=dataops-backups
BACKUP_RETENTION_DAYS=7

AWS_ACCESS_KEY_ID=TU_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=TU_SECRET_KEY
AWS_REGION=us-east-2
AWS_BUCKET=tu-bucket-s3

JWT_SECRET_KEY=dataops_super_secret_key_2026
PASSWORD_SECRET=dataops_password_secret_2026

ALERT_EMAIL_ENABLED=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=correo_origen@gmail.com
SMTP_PASSWORD=app_password
ALERT_EMAIL_TO=correo_destino@gmail.com
```

El archivo `.env` no debe subirse al repositorio.

## Archivo `.gitignore` recomendado

```txt
.env
node_modules/
frontend/node_modules/
__pycache__/
*.pyc
.venv/
backups/
```

## Ejecución con Docker

Desde la raíz del proyecto:

```cmd
docker compose up --build
```

Servicios principales:

- API FastAPI: `http://localhost:8000`
- Swagger/OpenAPI: `http://localhost:8000/docs`
- PostgreSQL: puerto `5432`
- Redis: puerto `6379`

## Ejecución del frontend

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

## Autenticación JWT

La autenticación JWT es obligatoria para los endpoints principales.

Flujo:

1. El usuario inicia sesión mediante `/token`.
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

Endpoints protegidos:

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
```

## Módulo 1: Registro de motores

Permite registrar motores de base de datos dentro del sistema.

Motores permitidos:

- PostgreSQL
- SQL Server
- Oracle

Endpoint principal:

```txt
POST /connections
GET /connections
```

El esquema valida que el campo `motor` solo acepte valores definidos por el lineamiento del proyecto.

## Módulo 2: Health Check automático

Se implementó captura automática de métricas mediante APScheduler.

Métricas capturadas:

- CPU
- Memoria
- Conexiones activas
- Locks
- Deadlocks
- Uso de disco

Frecuencia configurada:

```txt
Cada 1 minuto
```

Endpoints:

```txt
GET /metrics
GET /health-summary
```

## Módulo 3: Slow Query Monitor

Permite registrar consultas ejecutadas, medir duración y clasificarlas automáticamente.

Clasificación:

- Fast
- Medium
- Slow
- Critical

Endpoints:

```txt
POST /queries
GET /queries
GET /bi/top-slow-queries
```

El dashboard y Power BI muestran el ranking de las consultas con mayor duración promedio.

## Módulo 4: Concurrencia y Deadlocks

Se implementó una simulación de concurrencia con 100 usuarios simulados usando `ThreadPoolExecutor`.

El módulo ejecuta operaciones mixtas:

- INSERT
- UPDATE
- DELETE
- SELECT

Tipos de bloqueo registrados:

- SHARED
- EXCLUSIVE
- DEADLOCK
- TIMEOUT

Endpoints:

```txt
POST /concurrency/simulate
GET /concurrency/summary
GET /concurrency/logs
```

La evidencia principal del módulo es que el endpoint de simulación devuelve:

```txt
total_users: 100
total_transactions: 100
```

## Módulo 5: Backup, Recovery y Replicación hacia la Nube

Se implementó gestión de backups y replicación real hacia AWS S3.

Tipos de backup:

- FULL
- DIFF
- INC

Snapshots:

- PRE_DEPLOY
- PRE_TEST
- PRE_IMPORT

Funciones implementadas:

- Registro en `backup_history`
- Generación de archivo local
- Hash SHA256
- Subida automática a AWS S3
- Registro de URL remota
- Política de retención configurable
- Simulación de desastre
- Restauración con RPO/RTO
- SLA Sí/No

Endpoints:

```txt
POST /backup/full
POST /backup/diff
POST /backup/inc
POST /backup/snapshot/{snapshot_name}
POST /backup/simulate-disaster
POST /backup/restore
GET /backup/history
GET /backup/retention-policy
```

El backend está preparado para ejecutar un backup FULL cada 24 horas mediante APScheduler.

## Módulo 6: Replicación Distribuida

Se implementó simulación de replicación primario-réplica.

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

El frontend muestra:

- Eventos de replicación
- Último lag registrado
- Gráfica de lag de replicación

## Módulo 7: Caché con Redis

Redis se implementó como capa de caché para consultas frecuentes.

Comportamientos registrados:

- Cache HIT
- Cache MISS
- Tiempo de respuesta
- TTL
- Invalidación manual

Comparativa esperada:

- Sin caché: aproximadamente 400 ms
- Con caché: aproximadamente 40 ms

Endpoints:

```txt
GET /cache/query/{query_key}
DELETE /cache/invalidate/{query_key}
GET /cache/metrics
GET /cache/summary
```

El dashboard muestra el porcentaje de cache hit rate.

## Módulo 8: Business Intelligence

Se implementaron endpoints preparados para Power BI.

Vistas obligatorias cubiertas:

- Rendimiento temporal
- Heatmap de actividad
- Top queries lentas
- Estado de backups y SLA
- Disponibilidad global
- Lag de replicación
- Alertas

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

Power BI consume estos endpoints mediante `Authorization: Bearer TOKEN`.

Visualizaciones recomendadas:

- Gráfico de líneas para CPU, conexiones y locks
- Matriz para heatmap de actividad
- Tabla ranking de queries lentas
- Tarjetas SLA, RPO y RTO
- Gráfico de barras de disponibilidad
- Tabla de alertas

## Módulo 9: Motor de Alertas

Se implementó un motor de alertas configurable y automático.

Reglas mínimas:

| Condición | Acción | Severidad |
|---|---|---|
| CPU > 85% | Correo electrónico | Warning |
| Deadlocks > 3 | Alerta crítica en dashboard | Critical |
| Backup fallido | Alarma roja + correo | Critical |
| Lag replicación > 10 seg | Notificación en dashboard | Warning |
| Disco > 90% | Correo + alerta visual | Critical |
| Conexiones > umbral | Notificación automática | Warning |

Tablas:

- `alert_rules`
- `alert_log`

Cada alerta registra:

- Timestamp
- Condición disparadora
- Motor afectado
- Severidad
- Acción
- Estado de resolución

Endpoints:

```txt
POST /alerts/init-rules
GET /alerts/rules
PUT /alerts/rules/{rule_id}
POST /alerts/evaluate
GET /alerts/logs
PUT /alerts/resolve/{alert_id}
```

El motor de alertas puede ejecutarse automáticamente desde APScheduler.

El frontend muestra alertas recientes y un banner visual cuando existen alertas pendientes.

## Frontend React

El frontend implementa:

- Login con JWT
- Dashboard operativo
- Tarjetas de métricas
- Gráficas con Recharts
- Alertas recientes
- Estado de backups y SLA
- Métricas de Redis
- Métricas de replicación
- Diseño responsivo

Cards principales:

- Motores registrados
- CPU actual
- SLA Backups
- Cache Hit Rate
- Alertas registradas
- Backups totales
- Snapshots totales
- Eventos de replicación
- Último lag de replicación

## Power BI

Power BI se conecta a los endpoints protegidos usando token JWT.

Ejemplo de conexión:

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

Páginas recomendadas del dashboard:

- Resumen Ejecutivo
- Rendimiento Temporal
- Heatmap de Actividad
- Top Queries Lentas
- Backups y SLA
- Disponibilidad y Alertas

## Evidencias recomendadas

Capturas sugeridas para la entrega:

- Swagger con endpoints cargados
- Authorize JWT en Swagger
- Endpoint protegido sin token
- Endpoint protegido funcionando con token
- Dashboard React login
- Dashboard React principal
- Cards de backups, snapshots y replicación
- Gráfica de rendimiento temporal
- Gráfica de lag de replicación
- Alertas recientes
- AWS S3 mostrando archivos `.bak`
- Power BI con vistas obligatorias
- Redis cache HIT/MISS
- Simulación de concurrencia con 100 usuarios
- Logs de alertas generadas

## Comandos útiles

Levantar servicios:

```cmd
docker compose up --build
```

Detener servicios:

```cmd
docker compose down
```

Entrar a PostgreSQL:

```cmd
docker exec -it dataops_postgres psql -U dataops -d dataops_db
```

Ver contenedores:

```cmd
docker ps
```

Levantar frontend:

```cmd
cd frontend
npm run dev
```

## Seguridad

El proyecto usa variables de entorno para credenciales sensibles.

No se deben subir al repositorio:

- `.env`
- Credenciales AWS
- Passwords SMTP
- Tokens JWT
- `node_modules`

El backend protege rutas principales mediante JWT y Swagger permite autenticarse mediante el botón `Authorize`.

## Conclusión

DataOps Control Center integra monitoreo, análisis, respaldo, replicación, caché, alertas y visualización ejecutiva en una sola plataforma. El sistema demuestra prácticas de DataOps aplicadas a bases de datos empresariales, incluyendo automatización, observabilidad, recuperación ante fallos, seguridad, integración con nube y análisis mediante dashboards.
