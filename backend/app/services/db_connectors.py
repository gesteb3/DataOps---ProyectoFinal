from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import psycopg2

try:
    import pyodbc
except ImportError:
    pyodbc = None

try:
    import oracledb
except ImportError:
    oracledb = None


@dataclass
class ConnectionTestResult:
    status: str
    motor: str
    driver: str
    message: str
    version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "motor": self.motor,
            "driver": self.driver,
            "message": self.message,
            "version": self.version,
        }


def normalize_motor(motor: str) -> str:
    return motor.strip().lower().replace("_", " ").replace("-", " ")


def test_database_connection(
    motor: str,
    host: str,
    port: int,
    database_name: str,
    user_name: str,
    password: str,
    timeout_seconds: int = 5,
) -> dict[str, Any]:
    normalized_motor = normalize_motor(motor)

    if normalized_motor == "postgresql":
        return test_postgresql_connection(
            host=host,
            port=port,
            database_name=database_name,
            user_name=user_name,
            password=password,
            timeout_seconds=timeout_seconds,
        ).to_dict()

    if normalized_motor in {"sql server", "sqlserver", "mssql", "microsoft sql server"}:
        return test_sqlserver_connection(
            host=host,
            port=port,
            database_name=database_name,
            user_name=user_name,
            password=password,
            timeout_seconds=timeout_seconds,
        ).to_dict()

    if normalized_motor == "oracle":
        return test_oracle_connection(
            host=host,
            port=port,
            database_name=database_name,
            user_name=user_name,
            password=password,
            timeout_seconds=timeout_seconds,
        ).to_dict()

    return ConnectionTestResult(
        status="unsupported",
        motor=motor,
        driver="none",
        message=f"Motor no soportado para prueba de conexión: {motor}",
    ).to_dict()


def test_postgresql_connection(
    host: str,
    port: int,
    database_name: str,
    user_name: str,
    password: str,
    timeout_seconds: int = 5,
) -> ConnectionTestResult:
    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(
            host=host,
            port=port,
            dbname=database_name,
            user=user_name,
            password=password,
            connect_timeout=timeout_seconds,
        )
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]

        return ConnectionTestResult(
            status="connected",
            motor="PostgreSQL",
            driver="psycopg2",
            message="Conexión PostgreSQL exitosa.",
            version=version,
        )

    except Exception as exc:
        return ConnectionTestResult(
            status="error",
            motor="PostgreSQL",
            driver="psycopg2",
            message=str(exc),
        )

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def test_sqlserver_connection(
    host: str,
    port: int,
    database_name: str,
    user_name: str,
    password: str,
    timeout_seconds: int = 5,
) -> ConnectionTestResult:
    try:
        import pyodbc
    except ImportError:
        return ConnectionTestResult(
            status="driver_missing",
            motor="SQL Server",
            driver="pyodbc + ODBC Driver 18 for SQL Server",
            message="Falta instalar pyodbc o el ODBC Driver 18 for SQL Server dentro del contenedor.",
        )

    connection = None
    cursor = None

    try:
        connection_string = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={host},{port};"
            f"DATABASE={database_name};"
            f"UID={user_name};"
            f"PWD={password};"
            "Encrypt=yes;"
            "TrustServerCertificate=yes;"
            f"Connection Timeout={timeout_seconds};"
        )

        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]

        return ConnectionTestResult(
            status="connected",
            motor="SQL Server",
            driver="pyodbc + ODBC Driver 18 for SQL Server",
            message="Conexión SQL Server exitosa.",
            version=version,
        )

    except Exception as exc:
        return ConnectionTestResult(
            status="error",
            motor="SQL Server",
            driver="pyodbc + ODBC Driver 18 for SQL Server",
            message=str(exc),
        )

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def test_oracle_connection(
    host: str,
    port: int,
    database_name: str,
    user_name: str,
    password: str,
    timeout_seconds: int = 5,
) -> ConnectionTestResult:
    try:
        import oracledb
    except ImportError:
        return ConnectionTestResult(
            status="driver_missing",
            motor="Oracle",
            driver="python-oracledb thin mode",
            message="Falta instalar oracledb dentro del contenedor.",
        )

    connection = None
    cursor = None

    try:
        dsn = f"{host}:{port}/{database_name}"
        connection = oracledb.connect(
            user=user_name,
            password=password,
            dsn=dsn,
        )
        cursor = connection.cursor()
        cursor.execute("SELECT banner FROM v$version WHERE ROWNUM = 1")
        row = cursor.fetchone()
        version = row[0] if row else "Oracle conectado"

        return ConnectionTestResult(
            status="connected",
            motor="Oracle",
            driver="python-oracledb thin mode",
            message="Conexión Oracle exitosa.",
            version=version,
        )

    except Exception as exc:
        return ConnectionTestResult(
            status="error",
            motor="Oracle",
            driver="python-oracledb thin mode",
            message=str(exc),
        )

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
