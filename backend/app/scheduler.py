from datetime import datetime
import random

from apscheduler.schedulers.background import BackgroundScheduler

from app.database import SessionLocal
from app.models import DBMetric, Connection, JobAudit
from app.modules.alerts import evaluate_alerts_internal
from app.modules.backup import full_backup
from app.modules.replication import simulate_replication


scheduler = BackgroundScheduler()


def start_job_audit(db, job_name):
    audit = JobAudit(
        job_name=job_name,
        status="RUNNING",
        start_time=datetime.utcnow(),
        records_processed=0
    )

    db.add(audit)
    db.commit()
    db.refresh(audit)

    return audit


def finish_job_audit(db, audit, status, records_processed=0, error_message=None):
    audit.status = status
    audit.end_time = datetime.utcnow()
    audit.records_processed = records_processed
    audit.error_message = error_message

    db.commit()


def capture_metrics():
    db = SessionLocal()
    audit = None
    records_processed = 0

    try:
        audit = start_job_audit(db, "capture_metrics")

        connections = db.query(Connection).all()

        for connection in connections:
            metric = DBMetric(
                connection_id=connection.id,
                cpu=round(random.uniform(10, 90), 2),
                memory=round(random.uniform(20, 95), 2),
                connections=random.randint(1, 100),
                locks=random.randint(0, 10),
                deadlocks=random.randint(0, 6),
                disk_usage=round(random.uniform(30, 98), 2)
            )

            db.add(metric)
            records_processed += 1

        db.commit()

        finish_job_audit(
            db,
            audit,
            "SUCCESS",
            records_processed
        )

        print(f"Health Check ejecutado: {records_processed} motor(es) procesado(s)")

    except Exception as e:
        db.rollback()

        if audit:
            try:
                finish_job_audit(
                    db,
                    audit,
                    "FAILED",
                    records_processed,
                    str(e)
                )
            except Exception as audit_error:
                db.rollback()
                print(f"Error guardando auditoría del job: {audit_error}")

        print(f"Error en Health Check: {e}")

    finally:
        db.close()


def run_alert_engine():
    db = SessionLocal()
    audit = None
    alerts_count = 0

    try:
        audit = start_job_audit(db, "run_alert_engine")

        alerts = evaluate_alerts_internal()
        alerts_count = len(alerts)

        finish_job_audit(
            db,
            audit,
            "SUCCESS",
            alerts_count
        )

        if alerts_count:
            print(f"Motor de alertas ejecutado: {alerts_count} alerta(s) generada(s)")
        else:
            print("Motor de alertas ejecutado: sin alertas nuevas")

    except Exception as e:
        db.rollback()

        if audit:
            try:
                finish_job_audit(
                    db,
                    audit,
                    "FAILED",
                    alerts_count,
                    str(e)
                )
            except Exception as audit_error:
                db.rollback()
                print(f"Error guardando auditoría del motor de alertas: {audit_error}")

        print(f"Error en motor de alertas: {e}")

    finally:
        db.close()


scheduler.add_job(
    capture_metrics,
    "interval",
    minutes=5,
    id="capture_metrics",
    replace_existing=True
)

scheduler.add_job(
    simulate_replication,
    "interval",
    minutes=5,
    id="simulate_replication",
    replace_existing=True
)

scheduler.add_job(
    full_backup,
    "interval",
    hours=24,
    id="full_backup",
    replace_existing=True
)

scheduler.add_job(
    run_alert_engine,
    "interval",
    minutes=1,
    id="run_alert_engine",
    replace_existing=True
)