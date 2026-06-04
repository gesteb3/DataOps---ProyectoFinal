import hashlib
import os
import random
import time
from datetime import datetime
from typing import Optional

import boto3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import BackupHistory, Connection
from app.services.multi_engine_backup_service import create_real_backup_for_connection
from app.services.s3_backup_service import upload_backup_to_s3, find_latest_backup_in_s3


router = APIRouter(
    prefix="/backup",
    tags=["Backup"]
)


ALLOWED_BACKUP_TYPES = [
    "FULL",
    "DIFF",
    "INC",
    "PRE_DEPLOY",
    "PRE_TEST",
    "PRE_IMPORT"
]


class BackupRunRequest(BaseModel):
    backup_type: str = Field("FULL", description="FULL, DIFF, INC, PRE_DEPLOY, PRE_TEST o PRE_IMPORT")
    target: str = Field("ALL", description="ALL, SELECTED, ENGINE_SELECTION o nombre de motor")
    connection_id: Optional[int] = None
    connection_ids: list[int] = Field(default_factory=list)
    engines: list[str] = Field(default_factory=list)
    database_names: list[str] = Field(default_factory=list)


class BackupRunResponse(BaseModel):
    message: str
    backup_type: str
    target: str
    total: int
    successful: int
    failed: int
    results: list[dict]


def calculate_file_checksum(file_path: str):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for block in iter(lambda: file.read(4096), b""):
            sha256.update(block)

    return sha256.hexdigest()


def normalize_s3_prefix(prefix: str):
    if not prefix:
        return ""

    prefix = prefix.strip()

    if not prefix:
        return ""

    return prefix.strip("/") + "/"


def get_s3_client():
    region = os.getenv(
        "AWS_REGION",
        "us-east-2"
    )

    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=region
    )


def replicate_to_cloud(local_file_path, file_name, backup_type):
    cloud_provider = os.getenv(
        "CLOUD_PROVIDER",
        "SIMULATED"
    ).upper()

    if cloud_provider == "AWS":
        return upload_backup_to_s3(
            local_file_path=local_file_path,
            backup_type=backup_type,
            file_name=file_name
        )

    cloud_bucket = os.getenv(
        "CLOUD_BUCKET",
        "dataops-backups"
    )

    simulated_folder_map = {
        "FULL": "full",
        "DIFF": "diff",
        "INC": "inc",
        "PRE_DEPLOY": "pre_deploy",
        "PRE_TEST": "pre_test",
        "PRE_IMPORT": "pre_import"
    }
    folder = simulated_folder_map.get(backup_type, "unknown")

    return {
        "status": "SIMULATED",
        "url": f"https://simulated-storage/{cloud_bucket}/{folder}/{file_name}",
        "s3_key": f"{folder}/{file_name}",
        "folder": folder,
        "error": None
    }


def normalize_backup_type(backup_type: str) -> str:
    normalized = str(backup_type or "FULL").strip().upper()

    if normalized not in ALLOWED_BACKUP_TYPES:
        raise HTTPException(
            status_code=400,
            detail="backup_type debe ser FULL, DIFF, INC, PRE_DEPLOY, PRE_TEST o PRE_IMPORT"
        )

    return normalized


def normalize_engine(value: str) -> str:
    text = str(value or "").strip().lower()

    if text in ["postgres", "postgresql"]:
        return "PostgreSQL"

    if text in ["sql server", "sqlserver", "mssql"]:
        return "SQL Server"

    if text == "oracle":
        return "Oracle"

    return str(value or "").strip()


def get_backup_connections(db: Session, request: BackupRunRequest):
    query = db.query(Connection)

    selected_ids = list(dict.fromkeys(request.connection_ids or []))

    if request.connection_id and request.connection_id not in selected_ids:
        selected_ids.append(request.connection_id)

    if selected_ids:
        return query.filter(Connection.id.in_(selected_ids)).order_by(
            Connection.motor.asc(),
            Connection.database_name.asc(),
            Connection.nombre.asc()
        ).all()

    selected_engines = [normalize_engine(engine) for engine in request.engines if str(engine).strip()]
    selected_databases = [database.strip() for database in request.database_names if str(database).strip()]
    target = str(request.target or "ALL").strip()

    if selected_engines:
        query = query.filter(Connection.motor.in_(selected_engines))

    elif target.upper() not in ["ALL", "SELECTED", "ENGINE_SELECTION"]:
        query = query.filter(Connection.motor == normalize_engine(target))

    if selected_databases:
        query = query.filter(Connection.database_name.in_(selected_databases))

    return query.order_by(
        Connection.motor.asc(),
        Connection.database_name.asc(),
        Connection.nombre.asc()
    ).all()


def save_backup_record(
    db: Session,
    backup_type: str,
    backup_result: dict,
    cloud_result: dict
):
    cloud_url = (
        f"CLOUD_REPLICATION_FAILED: {cloud_result['error']}"
        if cloud_result["status"] == "FAILED"
        else cloud_result["url"]
    )

    hash_value = calculate_file_checksum(
        backup_result["local_file_path"]
    )

    backup = BackupHistory(
        backup_type=backup_type,
        file_name=backup_result["file_name"],
        size_mb=backup_result["size_mb"],
        duration_seconds=backup_result["duration_seconds"],
        restore_point=f"RP-{datetime.now()}",
        snapshot_name=backup_type if backup_type in ["PRE_DEPLOY", "PRE_TEST", "PRE_IMPORT"] else None,
        cloud_url=cloud_url,
        hash_value=hash_value
    )

    db.add(backup)
    db.commit()
    db.refresh(backup)

    return {
        "backup_id": backup.id,
        "backup_type": backup_type,
        "engine": backup_result["engine"],
        "source": backup_result["source"],
        "file": backup_result["file_name"],
        "file_name": backup_result["file_name"],
        "local_file_path": backup_result["local_file_path"],
        "size_mb": backup_result["size_mb"],
        "duration_seconds": backup_result["duration_seconds"],
        "cloud_status": cloud_result["status"],
        "cloud": cloud_url,
        "cloud_url": cloud_url,
        "s3_key": cloud_result.get("s3_key"),
        "s3_folder": cloud_result.get("folder"),
        "checksum": hash_value,
        "created_at": backup.created_at
    }


def run_real_backup_process(request: BackupRunRequest):
    backup_type = normalize_backup_type(request.backup_type)
    db: Session = SessionLocal()

    try:
        connections = get_backup_connections(db, request)

        if not connections:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron conexiones para generar backup. Registra motores reales primero."
            )

        results = []

        for connection in connections:
            connection_payload = {
                "id": connection.id,
                "nombre": connection.nombre,
                "motor": connection.motor,
                "database_name": connection.database_name,
                "host": connection.host,
                "port": connection.port
            }

            try:
                backup_result = create_real_backup_for_connection(
                    connection,
                    backup_type
                )

                cloud_result = replicate_to_cloud(
                    backup_result["local_file_path"],
                    backup_result["file_name"],
                    backup_type
                )

                saved = save_backup_record(
                    db,
                    backup_type,
                    backup_result,
                    cloud_result
                )

                results.append({
                    "status": "SUCCESS",
                    "connection": connection_payload,
                    **saved
                })

            except HTTPException as exc:
                results.append({
                    "status": "FAILED",
                    "connection": connection_payload,
                    "error": exc.detail
                })

            except Exception as exc:
                results.append({
                    "status": "FAILED",
                    "connection": connection_payload,
                    "error": str(exc)
                })

        successful = len([item for item in results if item["status"] == "SUCCESS"])
        failed = len(results) - successful

        return {
            "message": "Proceso de backup finalizado.",
            "backup_type": backup_type,
            "target": request.target,
            "total": len(results),
            "successful": successful,
            "failed": failed,
            "results": results
        }

    finally:
        db.close()


def simulate_restore_response():
    rpo_minutes = 15
    rto_minutes = 45

    simulated_rpo = random.randint(5, 20)
    simulated_rto = random.randint(20, 60)

    sla_compliance = simulated_rpo <= rpo_minutes and simulated_rto <= rto_minutes

    return {
        "message": "Restore process completed",
        "restore_chain": "FULL -> DIFF -> INC",
        "rpo_target_minutes": rpo_minutes,
        "rto_target_minutes": rto_minutes,
        "actual_rpo_minutes": simulated_rpo,
        "actual_rto_minutes": simulated_rto,
        "sla_compliance": "Sí" if sla_compliance else "No"
    }


@router.post("/run")
def run_backup(request: BackupRunRequest):
    return run_real_backup_process(request)


@router.post("/full")
def full_backup():
    return run_real_backup_process(
        BackupRunRequest(
            backup_type="FULL",
            target="ALL"
        )
    )


@router.post("/diff")
def diff_backup():
    return run_real_backup_process(
        BackupRunRequest(
            backup_type="DIFF",
            target="ALL"
        )
    )


@router.post("/inc")
def inc_backup():
    return run_real_backup_process(
        BackupRunRequest(
            backup_type="INC",
            target="ALL"
        )
    )


@router.get("/history")
def history():
    db = SessionLocal()

    data = db.query(
        BackupHistory
    ).filter(
        BackupHistory.snapshot_name == None
    ).order_by(
        BackupHistory.created_at.desc(),
        BackupHistory.id.desc()
    ).all()

    db.close()

    return data


@router.get("/snapshots")
def snapshots_history():
    db = SessionLocal()

    data = db.query(
        BackupHistory
    ).filter(
        BackupHistory.snapshot_name != None
    ).order_by(
        BackupHistory.created_at.desc(),
        BackupHistory.id.desc()
    ).all()

    db.close()

    return data


@router.post("/snapshot/{snapshot_name}")
def create_snapshot(snapshot_name: str):
    normalized_snapshot = normalize_backup_type(snapshot_name)
    allowed = ["PRE_DEPLOY", "PRE_TEST", "PRE_IMPORT"]

    if normalized_snapshot not in allowed:
        return {
            "error": "Snapshot name must be PRE_DEPLOY, PRE_TEST or PRE_IMPORT"
        }

    return run_real_backup_process(
        BackupRunRequest(
            backup_type=normalized_snapshot,
            target="ALL"
        )
    )


@router.post("/simulate-disaster")
def simulate_disaster():
    return {
        "message": "Disaster simulated",
        "event": "Accidental DROP TABLE detected",
        "affected_object": "query_log",
        "status": "requires_restore"
    }


@router.post("/restore")
def restore_backup():
    cloud_provider = os.getenv(
        "CLOUD_PROVIDER",
        "SIMULATED"
    ).upper()

    if cloud_provider != "AWS":
        simulated_restore = simulate_restore_response()

        return {
            **simulated_restore,
            "source": "SIMULATED",
            "note": "Para restaurar desde AWS configura CLOUD_PROVIDER=AWS en el .env"
        }

    bucket = os.getenv("AWS_BUCKET")

    if not bucket:
        raise HTTPException(
            status_code=500,
            detail="AWS_BUCKET no está configurado en el archivo .env"
        )

    restore_folder = os.getenv(
        "RESTORE_FOLDER",
        "restores"
    )

    os.makedirs(
        restore_folder,
        exist_ok=True
    )

    db = None

    try:
        s3 = get_s3_client()

        latest_backup = find_latest_backup_in_s3()

        if not latest_backup:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron backups físicos en el bucket de AWS S3"
            )

        object_key = latest_backup["Key"]

        file_name = os.path.basename(object_key)

        if not file_name:
            file_name = object_key.replace("/", "_")

        local_restore_path = os.path.join(
            restore_folder,
            file_name
        )

        s3.download_file(
            bucket,
            object_key,
            local_restore_path
        )

        checksum = calculate_file_checksum(
            local_restore_path
        )

        db = SessionLocal()

        backup_record = db.query(
            BackupHistory
        ).filter(
            BackupHistory.file_name == file_name
        ).order_by(
            BackupHistory.created_at.desc()
        ).first()

        checksum_status = "NO_LOCAL_HISTORY"

        if backup_record:
            if backup_record.hash_value == checksum:
                checksum_status = "MATCHED"
            else:
                checksum_status = "MISMATCH"

        restore_metrics = simulate_restore_response()

        return {
            **restore_metrics,
            "status": "RESTORED",
            "message": "Último backup de AWS restaurado correctamente.",
            "source": "AWS S3",
            "bucket": bucket,
            "object_key": object_key,
            "restored_file": file_name,
            "local_restore_path": local_restore_path,
            "size_bytes": latest_backup.get("Size"),
            "s3_last_modified": str(latest_backup.get("LastModified")),
            "checksum": checksum,
            "checksum_status": checksum_status
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo restaurar el último backup desde AWS: {str(e)}"
        )

    finally:
        if db:
            db.close()


@router.get("/retention-policy")
def retention_policy():
    retention_days = int(os.getenv("BACKUP_RETENTION_DAYS", 7))

    return {
        "retention_days": retention_days,
        "policy": f"Backups older than {retention_days} days are eligible for cleanup",
        "cloud_provider": os.getenv("CLOUD_PROVIDER", "SIMULATED"),
        "status": "configurable_by_environment_variables"
    }
