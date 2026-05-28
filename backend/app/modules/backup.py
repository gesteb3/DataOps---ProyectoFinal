import os
import random
import hashlib
import time
import boto3
from datetime import datetime
from fastapi import APIRouter

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import BackupHistory


router=APIRouter(
    prefix="/backup",
    tags=["Backup"]
)

def calculate_file_checksum(file_path: str):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for block in iter(lambda: file.read(4096), b""):
            sha256.update(block)

    return sha256.hexdigest()


def create_hash(data):

    return hashlib.sha256(
        data.encode()
    ).hexdigest()

def replicate_to_cloud(local_file_path, file_name):

    cloud_provider = os.getenv(
        "CLOUD_PROVIDER",
        "SIMULATED"
    ).upper()

    if cloud_provider == "AWS":

        bucket = os.getenv("AWS_BUCKET")

        region = os.getenv(
            "AWS_REGION",
            "us-east-2"
        )

        if not bucket:
            return {
                "status": "FAILED",
                "url": None,
                "error": "AWS_BUCKET no está configurado"
            }

        try:
            s3 = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=region
            )

            s3.upload_file(
                local_file_path,
                bucket,
                file_name
            )

            remote_object = s3.head_object(
                Bucket=bucket,
                Key=file_name
            )

            local_size = os.path.getsize(local_file_path)
            remote_size = remote_object.get("ContentLength", 0)

            if local_size != remote_size:
                return {
                    "status": "FAILED",
                    "url": None,
                    "error": "El tamaño del archivo en S3 no coincide con el archivo local"
                }

            return {
                "status": "SUCCESS",
                "url": f"https://{bucket}.s3.{region}.amazonaws.com/{file_name}",
                "error": None
            }

        except Exception as e:
            return {
                "status": "FAILED",
                "url": None,
                "error": str(e)
            }

    cloud_bucket = os.getenv(
        "CLOUD_BUCKET",
        "dataops-backups"
    )

    return {
        "status": "SIMULATED",
        "url": f"https://simulated-storage/{cloud_bucket}/{file_name}",
        "error": None
    }

def simulate_backup(backup_type):

    db:Session=SessionLocal()

    start=time.time()

    file_name=f"{backup_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"

    size=round(
        random.uniform(50,300),
        2
    )

    time.sleep(2)

    duration=round(
        time.time()-start,
        2
    )

    restore=f"RP-{datetime.now()}"
    
    backup_folder = "backups"

    os.makedirs(
        backup_folder,
        exist_ok=True
    )

    local_file_path = os.path.join(
        backup_folder,
        file_name
    )

    with open(local_file_path, "w") as backup_file:
        backup_file.write(
            f"Backup type: {backup_type}\n"
            f"Generated at: {datetime.now()}\n"
            f"Restore point: {restore}\n"
        )

    hash_value = calculate_file_checksum(local_file_path)

    cloud_result = replicate_to_cloud(
        local_file_path,
        file_name
    )

    if cloud_result["status"] == "FAILED":
        fake_cloud = f"CLOUD_REPLICATION_FAILED: {cloud_result['error']}"
    else:
        fake_cloud = cloud_result["url"]
        
    backup=BackupHistory(
    backup_type=backup_type,
    file_name=file_name,
    size_mb=size,
    duration_seconds=duration,
    restore_point=restore,
    snapshot_name=backup_type if backup_type in ["PRE_DEPLOY", "PRE_TEST", "PRE_IMPORT"] else None,
    cloud_url=fake_cloud,
    hash_value=hash_value
)

    db.add(backup)

    db.commit()

    db.close()

    return {
        "type": backup_type,
        "file": file_name,
        "size_mb": size,
        "duration_seconds": duration,
        "cloud_status": cloud_result["status"],
        "cloud": fake_cloud,
        "checksum": hash_value
    }


@router.post("/full")
def full_backup():

    return simulate_backup("FULL")


@router.post("/diff")
def diff_backup():

    return simulate_backup("DIFF")


@router.post("/inc")
def inc_backup():

    return simulate_backup("INC")


@router.get("/history")
def history():
    db = SessionLocal()

    data = db.query(
        BackupHistory
    ).filter(
        BackupHistory.snapshot_name.is_(None)
    ).order_by(
        BackupHistory.created_at.desc()
    ).all()

    db.close()

    return data


@router.get("/snapshots")
def snapshots_history():
    db = SessionLocal()

    data = db.query(
        BackupHistory
    ).filter(
        BackupHistory.snapshot_name.isnot(None)
    ).order_by(
        BackupHistory.created_at.desc()
    ).all()

    db.close()

    return data


@router.post("/snapshot/{snapshot_name}")
def create_snapshot(snapshot_name: str):
    allowed = ["PRE_DEPLOY", "PRE_TEST", "PRE_IMPORT"]

    if snapshot_name not in allowed:
        return {
            "error": "Snapshot name must be PRE_DEPLOY, PRE_TEST or PRE_IMPORT"
        }

    return simulate_backup(snapshot_name)


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


@router.get("/retention-policy")
def retention_policy():
    retention_days = int(os.getenv("BACKUP_RETENTION_DAYS", 7))

    return {
        "retention_days": retention_days,
        "policy": f"Backups older than {retention_days} days are eligible for cleanup",
        "cloud_provider": os.getenv("CLOUD_PROVIDER", "SIMULATED"),
        "status": "configurable_by_environment_variables"
    }