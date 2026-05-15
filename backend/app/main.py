from fastapi import FastAPI
import psycopg2

from app.database import engine
from app.models import Base, Connection, DBMetric
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas import ConnectionCreate
from app.security import encrypt_password
from app.scheduler import scheduler

app = FastAPI(
    title="DataOps Control Center",
    version="1.0"
)

Base.metadata.create_all(bind=engine)
scheduler.start()

@app.get("/")
def root():
    return {
        "message": "DataOps Control Center API running"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

@app.get("/db-test")
def db_test():
    try:
        connection = psycopg2.connect(
            host="postgres",
            port=5432,
            database="dataops_db",
            user="dataops",
            password="dataops123"
        )

        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()

        cursor.close()
        connection.close()

        return {
            "status": "connected",
            "database": "PostgreSQL",
            "version": db_version[0]
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
        
@app.post("/connections")
def create_connection(connection: ConnectionCreate):

    db: Session = SessionLocal()

    new_connection = Connection(
        nombre=connection.nombre,
        motor=connection.motor,
        host=connection.host,
        port=connection.port,
        database_name=connection.database_name,
        user_name=connection.user_name,
        encrypted_password=encrypt_password(
        connection.password
        ),
        status="ONLINE"
    )

    db.add(new_connection)
    db.commit()

    return {
        "message":"Motor registrado correctamente"
    }
    
@app.get("/connections")
def get_connections():

    db: Session = SessionLocal()

    connections = db.query(
        Connection
    ).all()

    return connections

@app.get("/metrics")
def get_metrics():

    db: Session = SessionLocal()

    metrics = db.query(
        DBMetric
    ).all()

    db.close()

    return metrics

@app.get("/health-summary")
def health_summary():

    db: Session = SessionLocal()

    total_connections = db.query(Connection).count()
    total_metrics = db.query(DBMetric).count()

    latest_metric = db.query(DBMetric).order_by(
        DBMetric.capture_time.desc()
    ).first()

    db.close()

    return {
        "registered_engines": total_connections,
        "captured_metrics": total_metrics,
        "latest_cpu": latest_metric.cpu if latest_metric else None,
        "latest_memory": latest_metric.memory if latest_metric else None,
        "latest_disk_usage": latest_metric.disk_usage if latest_metric else None,
        "status": "monitoring_active"
    }