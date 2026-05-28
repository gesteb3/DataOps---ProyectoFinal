# DataOps Control Center

DataOps Control Center es una plataforma de monitoreo, respaldo, análisis, caché, replicación y alertas para motores de bases de datos. El proyecto integra backend con FastAPI, base de datos PostgreSQL, Redis para caché, AWS S3 para replicación de backups, autenticación JWT, frontend React con Vite y dashboard analítico en Power BI.

## Objetivo del proyecto

El objetivo principal es centralizar operaciones críticas de administración de bases de datos, incluyendo monitoreo de salud, análisis de consultas lentas, concurrencia, backups, replicación, caché, visualización ejecutiva y alertas automáticas.

La plataforma permite registrar motores de base de datos, capturar métricas periódicas, analizar rendimiento, ejecutar simulaciones controladas, generar backups, replicarlos a la nube, consultar auditoría de procesos automáticos y visualizar el estado operativo desde un dashboard web y Power BI.

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
- Arquitectura basada en componentes

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

JWT_SECRET_KEY=CAMBIAR_EN_PRODUCCION
PASSWORD_SECRET=CAMBIAR_EN_PRODUCCION

ALERT_EMAIL_ENABLED=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=correo_origen@gmail.com
SMTP_PASSWORD=app_password
ALERT_EMAIL_TO=correo_destino@gmail.com
```

El archivo `.env` no debe subirse al repositorio.

## Variables de entorno del frontend

El frontend usa una variable opcional para definir la URL del backend:

```env
VITE_API_URL=http://localhost:8000
```

Si esta variable no existe, el frontend usa por defecto:

```txt
http://localhost:8000
```

Esta configuración se encuentra centralizada en:

```txt
frontend/src/api/client.js
```

El token JWT se guarda en `localStorage` y se envía automáticamente en las peticiones protegidas mediante:

```txt
Authorization: Bearer TOKEN
```

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
/jobs
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

El dashboard web consume `/health-summary` para mostrar las cards principales del sistema.

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
GET /backup/snapshots
GET /backup/retention-policy
GET /bi/backup-sla
```

El backend está preparado para ejecutar un backup FULL cada 24 horas mediante APScheduler.

El frontend muestra:

- Historial de backups
- Snapshots generados
- Estado de cumplimiento SLA
- RPO objetivo
- RTO objetivo
- Último backup registrado

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
- Tabla de estados recientes

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

El dashboard muestra el porcentaje de cache hit rate, cantidad de hits y cantidad de misses.

## Módulo 8: Business Intelligence

Se implementaron endpoints preparados para Power BI y para el dashboard React.

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

Power BI consume estos endpoints mediante:

```txt
Authorization: Bearer TOKEN
```

Visualizaciones recomendadas:

- Gráfico de líneas para CPU, memoria, disco y conexiones
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
PUT /alerts/resolve-all
```

El motor de alertas puede ejecutarse automáticamente desde APScheduler.

El frontend muestra alertas recientes, un banner visual cuando existen alertas críticas pendientes y permite resolver todas las alertas pendientes desde el dashboard.

## Auditoría de procesos automáticos

El sistema registra la ejecución de procesos automáticos para evidenciar el funcionamiento de tareas programadas.

Endpoint:

```txt
GET /jobs/audit
```

Este endpoint permite consultar registros de jobs como:

- Captura automática de métricas
- Evaluación automática de alertas
- Simulación de replicación
- Procesos de backup programado

El dashboard muestra esta información en una tabla de auditoría con estado, cantidad de registros procesados, hora de inicio, hora de fin y mensaje de error si aplica.

## Frontend React

El frontend fue rediseñado con una arquitectura más modular usando React, Vite, Axios y Recharts.

La nueva estructura separa responsabilidades en:

- `api/client.js`: cliente Axios centralizado para consumir el backend.
- `components/`: componentes reutilizables como Sidebar, Header, StatCard, ChartCard y DataTable.
- `pages/`: pantallas principales como Login y Dashboard.
- `index.css`: estilos globales del dashboard responsivo.

Funcionalidades implementadas:

- Login con JWT usando `POST /token`.
- Token guardado en `localStorage`.
- Envío automático del encabezado `Authorization: Bearer TOKEN`.
- Dashboard administrativo con sidebar lateral y header superior.
- Cards de resumen del sistema.
- Gráficas con Recharts.
- Tablas para backups, snapshots, alertas, replicación, queries lentas y auditoría.
- Botón para actualizar el dashboard manualmente.
- Actualización automática del dashboard.
- Botón para cerrar sesión.
- Botón para resolver todas las alertas pendientes.
- Manejo de errores por sección.
- Carga de datos usando `Promise.allSettled()` para evitar que falle todo el dashboard si un endpoint no responde.
- Diseño responsivo para pantallas grandes y pequeñas.

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

Cards principales:

- Motores registrados
- Métricas capturadas
- CPU actual
- Disco actual
- SLA Backups
- Cache Hit Rate
- Alertas pendientes
- Último lag de replicación

Secciones principales del dashboard:

- Resumen general
- Rendimiento temporal
- Disponibilidad por motor
- Lag de replicación
- Top queries lentas
- Alertas registradas
- Estado de replicación
- Backups y cumplimiento SLA
- Auditoría de jobs automáticos

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
- Login del dashboard React
- Nuevo dashboard React con sidebar lateral
- Header superior del dashboard
- Cards principales del dashboard
- Gráfica de rendimiento temporal
- Gráfica de disponibilidad por motor
- Gráfica de lag de replicación
- Tabla de top 10 queries lentas
- Tabla de alertas registradas
- Botón para resolver todas las alertas
- Tabla de backups
- Tabla de snapshots
- Tabla de auditoría de jobs automáticos
- Botón de actualización manual
- Vista responsive del dashboard
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
npm install
npm run dev
```

Ejecutar frontend con variable de entorno opcional:

```cmd
cd frontend
set VITE_API_URL=http://localhost:8000
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
- Archivos de entorno reales

El backend protege rutas principales mediante JWT y Swagger permite autenticarse mediante el botón `Authorize`.

El frontend conserva la autenticación JWT, guarda el token en `localStorage` y lo envía automáticamente en cada petición protegida.

## Mejoras visuales implementadas

Se rediseñó el frontend para que el sistema tenga una apariencia más moderna y profesional.

Mejoras principales:

- Sidebar lateral fijo.
- Header superior con acciones rápidas.
- Cards de resumen más limpias.
- Gráficas integradas con Recharts.
- Tablas administrativas más legibles.
- Estado visual para alertas críticas.
- Botón para resolver alertas pendientes.
- Actualización automática del dashboard.
- Manejo de errores por sección.
- Diseño responsivo.
- Separación del código en componentes reutilizables.

Esta mejora permite que el dashboard sea más claro para monitoreo operativo y más presentable para una exposición universitaria.

## Conclusión

DataOps Control Center integra monitoreo, análisis, respaldo, replicación, caché, alertas, auditoría y visualización ejecutiva en una sola plataforma. El sistema demuestra prácticas de DataOps aplicadas a bases de datos empresariales, incluyendo automatización, observabilidad, recuperación ante fallos, seguridad, integración con nube y análisis mediante dashboards.

