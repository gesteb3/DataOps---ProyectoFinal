import os
from typing import Any

import psycopg2


LAG_SCENARIOS = {
    "normal": {
        "scenario": "Carga normal",
        "lag_seconds": 2,
        "status": "Aceptable"
    },
    "media": {
        "scenario": "Carga media",
        "lag_seconds": 5,
        "status": "Advertencia"
    },
    "alta": {
        "scenario": "Carga alta",
        "lag_seconds": 20,
        "status": "Crítico"
    },
}


def classify_lag(lag_seconds: float) -> str:
    if lag_seconds <= 2:
        return "Aceptable"

    if lag_seconds <= 5:
        return "Advertencia"

    return "Crítico"


def get_lag_scenario(level: str) -> dict[str, Any]:
    normalized_level = level.strip().lower()

    if normalized_level not in LAG_SCENARIOS:
        raise ValueError("Escenario inválido. Usa normal, media o alta.")

    return LAG_SCENARIOS[normalized_level]


def measure_postgres_replication_lag() -> dict[str, Any]:
    host = os.getenv("REPLICA_DB_HOST", "postgres_replica")
    port = int(os.getenv("REPLICA_DB_PORT", "5432"))
    database = os.getenv("REPLICA_DB_NAME", "dataops_db")
    user = os.getenv("REPLICA_DB_USER", "dataops")
    password = os.getenv("REPLICA_DB_PASSWORD", "dataops123")

    query = """
        SELECT
            CASE
                WHEN pg_last_wal_receive_lsn() = pg_last_wal_replay_lsn()
                    THEN 0
                WHEN pg_last_xact_replay_timestamp() IS NULL
                    THEN 0
                ELSE EXTRACT(EPOCH FROM now() - pg_last_xact_replay_timestamp())
            END AS lag_seconds;
    """

    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(
            host=host,
            port=port,
            dbname=database,
            user=user,
            password=password,
            connect_timeout=5,
        )
        cursor = connection.cursor()
        cursor.execute(query)
        row = cursor.fetchone()
        lag_seconds = round(float(row[0] or 0), 2)

        return {
            "scenario": "Medición real PostgreSQL réplica",
            "lag_seconds": lag_seconds,
            "status": classify_lag(lag_seconds),
            "source": "REAL_POSTGRES_REPLICA"
        }

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
