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