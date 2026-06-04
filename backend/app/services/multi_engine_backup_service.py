import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

import oracledb
import pyodbc
from fastapi import HTTPException

from app.security import decrypt_password


BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "/app/backups"))
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

WINDOWS_BACKUP_DIR = os.getenv(
    "WINDOWS_BACKUP_DIR",
    r"C:\DataOpsBackups"
)

ORACLE_DIRECTORY_OBJECT = os.getenv(
    "ORACLE_DIRECTORY_OBJECT",
    "DATAOPS_BACKUP_DIR"
)


SUPPORTED_ENGINES = {
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "sql server": "SQL Server",
    "sqlserver": "SQL Server",
    "mssql": "SQL Server",
    "oracle": "Oracle",
}


def normalize_motor(motor: str) -> str:
    value = str(motor or "").strip().lower()

    if value in SUPPORTED_ENGINES:
        return SUPPORTED_ENGINES[value]

    raise HTTPException(
        status_code=400,
        detail=f"Motor no soportado para backup real: {motor}"
    )


def safe_name(value: str) -> str:
    clean = str(value or "sin_nombre").strip()

    for char in [" ", "\\", "/", ":", ".", "[", "]", "(", ")"]:
        clean = clean.replace(char, "_")

    return clean[:120]


def get_plain_password(connection) -> str:
    try:
        return decrypt_password(connection.encrypted_password)

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo descifrar la contraseña de {connection.nombre}: {str(exc)}"
        ) from exc


def build_file_names(connection, backup_type: str, extension: str):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    motor = safe_name(normalize_motor(connection.motor))
    database = safe_name(connection.database_name)
    name = safe_name(connection.nombre)

    file_name = f"{backup_type}_{motor}_{database}_{name}_{timestamp}.{extension}"

    container_path = BACKUP_DIR / file_name
    windows_path = f"{WINDOWS_BACKUP_DIR}\\{file_name}"

    return file_name, str(container_path), windows_path


def require_command(command_name: str):
    if shutil.which(command_name):
        return

    raise HTTPException(
        status_code=500,
        detail=f"No se encontró el comando requerido en el contenedor: {command_name}"
    )


def create_postgres_backup(connection, backup_type: str):
    require_command("pg_dump")

    password = get_plain_password(connection)

    file_name, container_path, _ = build_file_names(
        connection,
        backup_type,
        "dump"
    )

    env = os.environ.copy()
    env["PGPASSWORD"] = password

    command = [
        "pg_dump",
        "-h", connection.host,
        "-p", str(connection.port),
        "-U", connection.user_name,
        "-d", connection.database_name,
        "-Fc",
        "-f", container_path
    ]

    start = time.time()

    result = subprocess.run(
        command,
        env=env,
        capture_output=True,
        text=True,
        timeout=300
    )

    duration = round(time.time() - start, 2)

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Error generando backup PostgreSQL con pg_dump: {result.stderr}"
        )

    size_mb = round(os.path.getsize(container_path) / (1024 * 1024), 4)

    return {
        "engine": "PostgreSQL",
        "file_name": file_name,
        "local_file_path": container_path,
        "size_mb": size_mb,
        "duration_seconds": duration,
        "source": "REAL_PG_DUMP"
    }


def create_sqlserver_backup(connection, backup_type: str):
    password = get_plain_password(connection)

    extension = "trn" if backup_type == "INC" else "bak"

    file_name, container_path, windows_path = build_file_names(
        connection,
        backup_type,
        extension
    )

    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={connection.host},{connection.port};"
        f"DATABASE={connection.database_name};"
        f"UID={connection.user_name};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
        "Encrypt=no;"
    )

    if backup_type == "DIFF":
        sql = f"""
        BACKUP DATABASE [{connection.database_name}]
        TO DISK = N'{windows_path}'
        WITH DIFFERENTIAL, INIT, CHECKSUM, STATS = 10;
        """

    elif backup_type == "INC":
        sql = f"""
        BACKUP LOG [{connection.database_name}]
        TO DISK = N'{windows_path}'
        WITH INIT, CHECKSUM, STATS = 10;
        """

    else:
        sql = f"""
        BACKUP DATABASE [{connection.database_name}]
        TO DISK = N'{windows_path}'
        WITH INIT, CHECKSUM, STATS = 10;
        """

    start = time.time()

    try:
        sql_conn = pyodbc.connect(
            conn_str,
            autocommit=True,
            timeout=25
        )

        cursor = sql_conn.cursor()
        cursor.execute(sql)

        while cursor.nextset():
            pass

        cursor.close()
        sql_conn.close()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Error generando backup SQL Server. "
                "Verifica TCP/IP, puerto, usuario, permisos de BACKUP DATABASE "
                "y permisos sobre C:\\DataOpsBackups. "
                f"Detalle: {str(exc)}"
            )
        ) from exc

    duration = round(time.time() - start, 2)

    if not os.path.exists(container_path):
        raise HTTPException(
            status_code=500,
            detail=(
                "SQL Server ejecutó el BACKUP, pero la API no encontró el archivo. "
                "Verifica que C:\\DataOpsBackups esté montado como /app/backups "
                "y que el servicio de SQL Server tenga permisos para escribir ahí."
            )
        )

    size_mb = round(os.path.getsize(container_path) / (1024 * 1024), 4)

    return {
        "engine": "SQL Server",
        "file_name": file_name,
        "local_file_path": container_path,
        "size_mb": size_mb,
        "duration_seconds": duration,
        "source": "REAL_SQLSERVER_BACKUP_DATABASE"
    }


def create_oracle_backup(connection, backup_type: str):
    password = get_plain_password(connection)

    file_name, container_path, _ = build_file_names(
        connection,
        backup_type,
        "dmp"
    )

    log_name = file_name.replace(".dmp", ".log")

    dsn = oracledb.makedsn(
        connection.host,
        int(connection.port),
        service_name=connection.database_name
    )

    plsql = """
    DECLARE
        h1 NUMBER;
        v_state VARCHAR2(100);
    BEGIN
        h1 := DBMS_DATAPUMP.OPEN(
            operation => 'EXPORT',
            job_mode => 'SCHEMA'
        );

        DBMS_DATAPUMP.ADD_FILE(
            handle => h1,
            filename => :dump_file,
            directory => :directory_name,
            filetype => DBMS_DATAPUMP.KU$_FILE_TYPE_DUMP_FILE,
            reusefile => 1
        );

        DBMS_DATAPUMP.ADD_FILE(
            handle => h1,
            filename => :log_file,
            directory => :directory_name,
            filetype => DBMS_DATAPUMP.KU$_FILE_TYPE_LOG_FILE,
            reusefile => 1
        );

        DBMS_DATAPUMP.METADATA_FILTER(
            handle => h1,
            name => 'SCHEMA_EXPR',
            value => '= ''' || USER || ''''
        );

        DBMS_DATAPUMP.START_JOB(h1);

        DBMS_DATAPUMP.WAIT_FOR_JOB(
            handle => h1,
            job_state => v_state
        );

        DBMS_DATAPUMP.DETACH(h1);
    END;
    """

    start = time.time()

    try:
        oracle_conn = oracledb.connect(
            user=connection.user_name,
            password=password,
            dsn=dsn
        )

        cursor = oracle_conn.cursor()

        cursor.execute(
            plsql,
            dump_file=file_name,
            log_file=log_name,
            directory_name=ORACLE_DIRECTORY_OBJECT
        )

        cursor.close()
        oracle_conn.close()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Error generando backup Oracle Data Pump. "
                "Verifica usuario, contraseña, service name, permisos Data Pump "
                "y DIRECTORY DATAOPS_BACKUP_DIR. "
                f"Detalle: {str(exc)}"
            )
        ) from exc

    duration = round(time.time() - start, 2)

    if not os.path.exists(container_path):
        raise HTTPException(
            status_code=500,
            detail=(
                "Oracle ejecutó Data Pump, pero la API no encontró el archivo. "
                "Verifica que DATAOPS_BACKUP_DIR apunte a C:\\DataOpsBackups "
                "y que docker-compose tenga montado C:/DataOpsBackups:/app/backups."
            )
        )

    size_mb = round(os.path.getsize(container_path) / (1024 * 1024), 4)

    return {
        "engine": "Oracle",
        "file_name": file_name,
        "local_file_path": container_path,
        "size_mb": size_mb,
        "duration_seconds": duration,
        "source": "REAL_ORACLE_DATAPUMP"
    }


def create_real_backup_for_connection(connection, backup_type: str):
    motor = normalize_motor(connection.motor)
    backup_type = str(backup_type or "FULL").upper()

    if backup_type not in ["FULL", "DIFF", "INC", "PRE_DEPLOY", "PRE_TEST", "PRE_IMPORT"]:
        raise HTTPException(
            status_code=400,
            detail="Tipo de backup inválido. Usa FULL, DIFF, INC, PRE_DEPLOY, PRE_TEST o PRE_IMPORT."
        )

    if motor == "PostgreSQL":
        return create_postgres_backup(connection, backup_type)

    if motor == "SQL Server":
        return create_sqlserver_backup(connection, backup_type)

    if motor == "Oracle":
        return create_oracle_backup(connection, backup_type)

    raise HTTPException(
        status_code=400,
        detail=f"Motor no soportado para backup real: {connection.motor}"
    )