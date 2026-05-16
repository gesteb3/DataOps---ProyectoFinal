from fastapi import FastAPI
import psycopg2

from app.database import engine
from app.models import Base, Connection, DBMetric, QueryLog, BackupHistory, User
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas import ConnectionCreate, QueryLogCreate, LoginData
from app.security import encrypt_password
from app.scheduler import scheduler
from app.modules.concurrency import router as concurrency_router
from app.modules.backup import router as backup_router
from app.jwt_security import create_access_token
from app.modules.replication import router as replication_router
from app.modules.cache import router as cache_router


app = FastAPI(
    title="DataOps Control Center",
    version="1.0"
)

app.include_router(
    replication_router
)
app.include_router(backup_router)
app.include_router(concurrency_router)
Base.metadata.create_all(bind=engine)
app.include_router(cache_router)
scheduler.start()

def classify_query(duration_ms: int):
    if duration_ms < 100:
        return "Fast"
    elif duration_ms <= 500:
        return "Medium"
    elif duration_ms <= 2000:
        return "Slow"
    else:
        return "Critical"

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
    
@app.post("/queries")
def create_query_log(query: QueryLogCreate):

    db: Session = SessionLocal()

    new_query = QueryLog(
        connection_id=query.connection_id,
        query_text=query.query_text,
        duration_ms=query.duration_ms,
        rows_returned=query.rows_returned,
        index_used=query.index_used,
        execution_plan=query.execution_plan,
        classification=classify_query(query.duration_ms)
    )

    db.add(new_query)
    db.commit()
    db.refresh(new_query)

    db.close()

    return {
        "message": "Consulta registrada correctamente",
        "classification": new_query.classification,
        "duration_ms": new_query.duration_ms
    }


@app.get("/queries")
def get_query_logs():

    db: Session = SessionLocal()

    queries = db.query(QueryLog).all()

    db.close()

    return queries

@app.post("/login")
def login(user:LoginData):

    db:Session=SessionLocal()

    existing_user=db.query(
        User
    ).filter(
        User.username==user.username
    ).first()

    if not existing_user:

        demo_user=User(
            username="admin",
            password="admin123"
        )

        db.add(demo_user)
        db.commit()

        existing_user=demo_user

    if(
        existing_user.password
        !=user.password
    ):

        return{
            "error":"Credenciales inválidas"
        }

    token=create_access_token(
        {
            "sub":existing_user.username
        }
    )

    return{
        "access_token":token,
        "token_type":"bearer"
    }