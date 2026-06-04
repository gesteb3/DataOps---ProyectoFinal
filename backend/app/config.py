import os


class Settings:
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://dataops:dataops123@postgres:5432/dataops_db"
    )

    REDIS_HOST = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "60"))

    CLOUD_PROVIDER = os.getenv("CLOUD_PROVIDER", "SIMULATED")
    CLOUD_BUCKET = os.getenv("CLOUD_BUCKET", "dataops-backups")
    AWS_BUCKET = os.getenv("AWS_BUCKET")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-2")
    AWS_BACKUP_PREFIX = os.getenv("AWS_BACKUP_PREFIX", "")

    REPLICA_DB_HOST = os.getenv("REPLICA_DB_HOST", "postgres_replica")
    REPLICA_DB_PORT = int(os.getenv("REPLICA_DB_PORT", "5432"))
    REPLICA_DB_NAME = os.getenv("REPLICA_DB_NAME", "dataops_db")
    REPLICA_DB_USER = os.getenv("REPLICA_DB_USER", "dataops")
    REPLICA_DB_PASSWORD = os.getenv("REPLICA_DB_PASSWORD", "dataops123")

    BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))

    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173"
    ).split(",")


settings = Settings()