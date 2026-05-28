import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import psycopg2
from fastapi import APIRouter, Query
from sqlalchemy import Column, DateTime, Integer, String, text
from sqlalchemy.orm import Session

from app.config import settings
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


def get_resolution_strategy(lock_type: str) -> str:
    if lock_type == "DEADLOCK":
        return "ROLLBACK_AND_RETRY_SIMULATED"
    if lock_type == "TIMEOUT":
        return "CANCEL_WAITING_TRANSACTION_SIMULATED"
    return "NO_RESOLUTION_REQUIRED"


def save_tx_log(
    session_id: str,
    operation: str,
    start_time: datetime,
    end_time: datetime,
    wait_time: int,
    lock_type: str,
):
    db: Session = SessionLocal()

    try:
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

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def simulate_user_transaction(
    user_number: int,
    force_deadlock: bool = False,
    force_timeout: bool = False,
):
    try:
        session_id = f"SESSION-{user_number}"
        operation = random.choice(OPERATIONS)
        start_time = datetime.now()

        wait_time = random.randint(20, 900)
        time.sleep(wait_time / 1000)

        probability = random.randint(1, 100)

        if force_deadlock:
            lock_type = "DEADLOCK"
        elif force_timeout:
            lock_type = "TIMEOUT"
        elif probability <= 10:
            lock_type = "DEADLOCK"
        elif probability <= 20:
            lock_type = "TIMEOUT"
        elif operation in ["INSERT", "UPDATE", "DELETE"]:
            lock_type = "EXCLUSIVE"
        else:
            lock_type = "SHARED"

        end_time = datetime.now()

        save_tx_log(
            session_id=session_id,
            operation=operation,
            start_time=start_time,
            end_time=end_time,
            wait_time=wait_time,
            lock_type=lock_type,
        )

        return {
            "session": session_id,
            "operation": operation,
            "wait_time": wait_time,
            "lock_type": lock_type,
            "resolution_strategy": get_resolution_strategy(lock_type),
        }

    except Exception as e:
        return {
            "session": f"SESSION-{user_number}",
            "error": str(e),
        }


@router.post("/simulate")
def simulate_concurrency(
    force_deadlock: bool = Query(
        False,
        description="Si es true, fuerza que las 100 transacciones se registren como DEADLOCK para una demo controlada.",
    ),
    force_timeout: bool = Query(
        False,
        description="Si es true, fuerza que las 100 transacciones se registren como TIMEOUT para una demo controlada.",
    ),
):
    total_users = 100
    results = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(simulate_user_transaction, i, force_deadlock, force_timeout)
            for i in range(1, total_users + 1)
        ]

        for future in as_completed(futures):
            results.append(future.result())

    deadlocks = len([r for r in results if r.get("lock_type") == "DEADLOCK"])
    timeouts = len([r for r in results if r.get("lock_type") == "TIMEOUT"])

    return {
        "message": "Concurrency simulation completed",
        "mode": "forced_deadlock" if force_deadlock else "forced_timeout" if force_timeout else "random_simulation",
        "total_users": total_users,
        "total_transactions": len(results),
        "deadlocks_detected": deadlocks,
        "timeouts_detected": timeouts,
        "automatic_resolution": "Deadlocks and timeouts were detected, logged and assigned a simulated resolution strategy.",
        "results": results,
    }


def prepare_deadlock_demo_table():
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS deadlock_demo (
                    id INTEGER PRIMARY KEY,
                    value INTEGER NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO deadlock_demo (id, value)
                VALUES (1, 100), (2, 200)
                ON CONFLICT (id) DO NOTHING
                """
            )
        )


def run_real_deadlock_transaction(
    session_id: str,
    first_row_id: int,
    second_row_id: int,
    barrier: threading.Barrier,
    results: list,
):
    connection = None
    cursor = None
    start_time = datetime.now()

    try:
        connection = psycopg2.connect(settings.DATABASE_URL)
        connection.autocommit = False
        cursor = connection.cursor()

        cursor.execute("SET lock_timeout = '5000ms';")
        cursor.execute(
            "UPDATE deadlock_demo SET value = value + 1 WHERE id = %s;",
            (first_row_id,),
        )

        barrier.wait(timeout=5)
        time.sleep(0.5)

        cursor.execute(
            "UPDATE deadlock_demo SET value = value + 1 WHERE id = %s;",
            (second_row_id,),
        )

        connection.commit()
        end_time = datetime.now()
        wait_time = int((end_time - start_time).total_seconds() * 1000)

        save_tx_log(session_id, "UPDATE", start_time, end_time, wait_time, "EXCLUSIVE")

        results.append(
            {
                "session": session_id,
                "result": "committed",
                "lock_type": "EXCLUSIVE",
                "resolution_strategy": "NO_RESOLUTION_REQUIRED",
            }
        )

    except psycopg2.errors.DeadlockDetected as exc:
        if connection:
            connection.rollback()

        end_time = datetime.now()
        wait_time = int((end_time - start_time).total_seconds() * 1000)
        save_tx_log(session_id, "UPDATE", start_time, end_time, wait_time, "DEADLOCK")

        results.append(
            {
                "session": session_id,
                "result": "rolled_back",
                "lock_type": "DEADLOCK",
                "resolution_strategy": "POSTGRESQL_ABORTED_ONE_TRANSACTION_AUTOMATICALLY",
                "error": str(exc).split("\n")[0],
            }
        )

    except Exception as exc:
        if connection:
            connection.rollback()

        end_time = datetime.now()
        wait_time = int((end_time - start_time).total_seconds() * 1000)
        save_tx_log(session_id, "UPDATE", start_time, end_time, wait_time, "TIMEOUT")

        results.append(
            {
                "session": session_id,
                "result": "rolled_back",
                "lock_type": "TIMEOUT",
                "resolution_strategy": "ROLLBACK_AFTER_ERROR",
                "error": str(exc).split("\n")[0],
            }
        )

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.post("/real-deadlock-postgres")
def simulate_real_postgres_deadlock():
    prepare_deadlock_demo_table()

    barrier = threading.Barrier(2)
    results = []

    thread_a = threading.Thread(
        target=run_real_deadlock_transaction,
        args=("REAL-DEADLOCK-A", 1, 2, barrier, results),
    )
    thread_b = threading.Thread(
        target=run_real_deadlock_transaction,
        args=("REAL-DEADLOCK-B", 2, 1, barrier, results),
    )

    thread_a.start()
    thread_b.start()
    thread_a.join(timeout=10)
    thread_b.join(timeout=10)

    deadlocks = len([item for item in results if item.get("lock_type") == "DEADLOCK"])
    timeouts = len([item for item in results if item.get("lock_type") == "TIMEOUT"])

    return {
        "message": "PostgreSQL real deadlock demo completed",
        "description": "Two transactions update the same rows in opposite order. PostgreSQL aborts one transaction to resolve the deadlock.",
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
            "automatic_resolution": "Deadlocks and timeouts were detected, logged and assigned a resolution strategy automatically.",
        }

    finally:
        db.close()
