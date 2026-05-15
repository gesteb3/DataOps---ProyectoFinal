import random
import hashlib
import time

from datetime import datetime
from fastapi import APIRouter

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import BackupHistory


router=APIRouter(
    prefix="/backup",
    tags=["Backup"]
)


def create_hash(data):

    return hashlib.sha256(
        data.encode()
    ).hexdigest()


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

    fake_cloud=f"https://cloud-storage/{file_name}"

    hash_value=create_hash(file_name)

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

    return{
        "type":backup_type,
        "file":file_name,
        "size_mb":size,
        "duration_seconds":duration,
        "cloud":fake_cloud
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

    db=SessionLocal()

    data=db.query(
        BackupHistory
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