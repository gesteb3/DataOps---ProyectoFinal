# Patch DataOps Control Center: filtro multi-selección + backups reales multi-motor

Este patch agrega:

- Filtro global elegante con selección múltiple de motores.
- Selección múltiple de bases de datos registradas.
- Botones FULL, DIFF e INC en la Top Bar para ejecutar backup sobre la selección actual.
- Endpoint `POST /backup/run`.
- Servicio multi-motor:
  - PostgreSQL: `pg_dump` real.
  - SQL Server: `BACKUP DATABASE`, `BACKUP DATABASE WITH DIFFERENTIAL` y `BACKUP LOG`.
  - Oracle: export real con `DBMS_DATAPUMP`.
- Historial ordenado del backup más reciente al más antiguo.
- Subida a AWS S3 respetando carpetas: `full/`, `diff/`, `inc/`, `pre_deploy/`, `pre_test/`, `pre_import/`.

## 1. Copiar archivos

Descomprime este ZIP encima de la raíz de tu proyecto `DataOps-Control-Center` y acepta reemplazar archivos.

## 2. Crear carpeta compartida en Windows

```powershell
mkdir C:\DataOpsBackups
```

El `docker-compose.yml` del patch monta esa carpeta así:

```yaml
- C:/DataOpsBackups:/app/backups
```

Eso permite que SQL Server y Oracle escriban en Windows, y que la API lea esos archivos desde Docker.

## 3. Variables recomendadas en `.env`

```env
BACKUP_DIR=/app/backups
WINDOWS_BACKUP_DIR=C:\DataOpsBackups
ORACLE_DIRECTORY_OBJECT=DATAOPS_BACKUP_DIR

CLOUD_PROVIDER=AWS
AWS_BUCKET=tu-bucket-real
AWS_REGION=us-east-2
AWS_BACKUP_PREFIX=
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
```

Deja `AWS_BACKUP_PREFIX=` vacío si quieres que en S3 queden exactamente las carpetas `full/`, `diff/`, `inc/`, `pre_deploy/`, `pre_test/` y `pre_import/`.

## 4. SQL Server local

Tu SQL Server local debe poder escribir en `C:\DataOpsBackups`.

En SSMS prueba:

```sql
USE master;
GO

BACKUP DATABASE [DataOpsTest]
TO DISK = N'C:\DataOpsBackups\prueba_sqlserver.bak'
WITH INIT, CHECKSUM;
GO
```

Si falla, dale permisos a la cuenta del servicio de SQL Server sobre esa carpeta.

Para DIFF se usa `BACKUP DATABASE WITH DIFFERENTIAL`.
Para INC se usa `BACKUP LOG`; esto requiere que la base esté en recovery model FULL y que exista un backup FULL previo.

## 5. Oracle XE local

Con `sqlplus / as sysdba` ejecuta:

```sql
CREATE OR REPLACE DIRECTORY DATAOPS_BACKUP_DIR AS 'C:\DataOpsBackups';
GRANT READ, WRITE ON DIRECTORY DATAOPS_BACKUP_DIR TO C##DATAOPS_USER;
GRANT DATAPUMP_EXP_FULL_DATABASE TO C##DATAOPS_USER;
```

En DataOps registra Oracle con:

```text
Host: host.docker.internal
Puerto: 1521
Service Name: XE
Usuario: C##DATAOPS_USER
Contraseña: DataOps123
```

## 6. Reconstruir

```powershell
docker compose down
docker compose up -d --build
```

Luego frontend:

```powershell
cd frontend
npm run dev
```

## 7. Probar desde Swagger

```json
POST /backup/run

{
  "backup_type": "FULL",
  "target": "ALL",
  "connection_ids": [],
  "engines": [],
  "database_names": []
}
```

Solo bases seleccionadas:

```json
{
  "backup_type": "FULL",
  "target": "SELECTED",
  "connection_ids": [1, 2],
  "engines": [],
  "database_names": []
}
```

Solo motores seleccionados:

```json
{
  "backup_type": "FULL",
  "target": "ENGINE_SELECTION",
  "connection_ids": [],
  "engines": ["PostgreSQL", "SQL Server"],
  "database_names": []
}
```

## 8. Commit sugerido

```powershell
git add backend/app/modules/backup.py backend/app/services/multi_engine_backup_service.py backend/app/services/s3_backup_service.py backend/app/main.py backend/Dockerfile docker-compose.yml frontend/src/api/client.js frontend/src/components/Header.jsx frontend/src/pages/Dashboard.jsx frontend/src/index.css

git commit -m "Agrega filtro multiple y backups reales multimotor"

git push
```
