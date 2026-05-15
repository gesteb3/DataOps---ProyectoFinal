from apscheduler.schedulers.background import BackgroundScheduler
from app.database import SessionLocal
from app.models import DBMetric, Connection
import random

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
                deadlocks=random.randint(0, 3),
                disk_usage=round(random.uniform(30, 90), 2)
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