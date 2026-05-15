import random
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import APIRouter
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine

router = APIRouter(prefix="/concurrency", tags=["Concurrency"])


class TxLog(Base):
    __tablename__ = "tx_log"

    id = Column(Integer, primary_key=True, index=True)
    session = Column(String, nullable=False)
    operation = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    wait_time = Column(Integer, nullable=False)
    lock_type = Column(String, nullable=False)


Base.metadata.create_all(bind=engine)


OPERATIONS = ["INSERT", "UPDATE", "DELETE", "SELECT"]
LOCK_TYPES = ["SHARED", "EXCLUSIVE", "DEADLOCK", "TIMEOUT"]


def simulate_user_transaction(user_number: int):
    db: Session = SessionLocal()

    try:
        session_id = f"SESSION-{user_number}"
        operation = random.choice(OPERATIONS)

        start_time = datetime.now()

        wait_time = random.randint(20, 900)
        time.sleep(wait_time / 1000)

        probability = random.randint(1, 100)

        if probability <= 10:
            lock_type = "DEADLOCK"
        elif probability <= 20:
            lock_type = "TIMEOUT"
        elif operation in ["INSERT", "UPDATE", "DELETE"]:
            lock_type = "EXCLUSIVE"
        else:
            lock_type = "SHARED"

        end_time = datetime.now()

        log = TxLog(
            session=session_id,
            operation=operation,
            start_time=start_time,
            end_time=end_time,
            wait_time=wait_time,
            lock_type=lock_type,
        )

        db.add(log)
        db.commit()

        return {
            "session": session_id,
            "operation": operation,
            "wait_time": wait_time,
            "lock_type": lock_type,
        }

    except Exception as e:
        db.rollback()
        return {
            "session": f"SESSION-{user_number}",
            "error": str(e),
        }

    finally:
        db.close()


@router.post("/simulate")
def simulate_concurrency():
    total_users = 100
    results = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(simulate_user_transaction, i)
            for i in range(1, total_users + 1)
        ]

        for future in as_completed(futures):
            results.append(future.result())

    deadlocks = len([r for r in results if r.get("lock_type") == "DEADLOCK"])
    timeouts = len([r for r in results if r.get("lock_type") == "TIMEOUT"])

    return {
        "message": "Concurrency simulation completed",
        "total_users": total_users,
        "total_transactions": len(results),
        "deadlocks_detected": deadlocks,
        "timeouts_detected": timeouts,
        "results": results,
    }


@router.get("/logs")
def get_tx_logs():
    db: Session = SessionLocal()

    try:
        logs = db.query(TxLog).order_by(TxLog.id.desc()).limit(200).all()

        return [
            {
                "id": log.id,
                "session": log.session,
                "operation": log.operation,
                "start_time": log.start_time,
                "end_time": log.end_time,
                "wait_time": log.wait_time,
                "lock_type": log.lock_type,
            }
            for log in logs
        ]

    finally:
        db.close()


@router.get("/summary")
def get_concurrency_summary():
    db: Session = SessionLocal()

    try:
        total = db.query(TxLog).count()
        deadlocks = db.query(TxLog).filter(TxLog.lock_type == "DEADLOCK").count()
        timeouts = db.query(TxLog).filter(TxLog.lock_type == "TIMEOUT").count()
        shared = db.query(TxLog).filter(TxLog.lock_type == "SHARED").count()
        exclusive = db.query(TxLog).filter(TxLog.lock_type == "EXCLUSIVE").count()

        return {
            "total_transactions": total,
            "shared_locks": shared,
            "exclusive_locks": exclusive,
            "deadlocks": deadlocks,
            "timeouts": timeouts,
            "automatic_resolution": "Deadlocks and timeouts were detected and logged automatically",
        }

    finally:
        db.close()