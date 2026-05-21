from app.modules.alerts import evaluate_alerts_internal
from apscheduler.schedulers.background import BackgroundScheduler
from app.database import SessionLocal
from app.models import DBMetric, Connection
import random
from app.modules.backup import full_backup
from app.modules.replication import simulate_replication

scheduler = BackgroundScheduler()

def capture_metrics():
    db = SessionLocal()

    try:
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

        db.commit()
        print("Health Check ejecutado")

    finally:
        db.close()

scheduler.add_job(
    capture_metrics,
    "interval",
    minutes=1
)

scheduler.add_job(
    simulate_replication,
    "interval",
    seconds=30
)

def run_alert_engine():

    try:
        alerts = evaluate_alerts_internal()

        if alerts:
            print(f"Motor de alertas ejecutado: {len(alerts)} alerta(s) generada(s)")
        else:
            print("Motor de alertas ejecutado: sin alertas nuevas")

    except Exception as e:
        print(f"Error en motor de alertas: {e}")


scheduler.add_job(
    run_alert_engine,
    "interval",
    minutes=1
)