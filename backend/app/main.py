from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
import psycopg2

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import engine
from app.database import SessionLocal
from app.models import Base, Connection, DBMetric, QueryLog, User, JobAudit
from app.schemas import ConnectionCreate, QueryLogCreate, LoginData
from app.security import decrypt_password, encrypt_password
from app.scheduler import scheduler
from app.jwt_security import create_access_token, get_current_user
from app.modules.concurrency import router as concurrency_router
from app.modules.backup import router as backup_router
from app.modules.replication import router as replication_router
from app.modules.cache import router as cache_router
from app.modules.bi import router as bi_router
from app.modules.alerts import router as alerts_router
from app.services.db_connectors import test_database_connection


app = FastAPI(
    title="DataOps Control Center",
    version="1.0"
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


app.include_router(
    replication_router,
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    bi_router,
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    backup_router,
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    concurrency_router,
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    cache_router,
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    alerts_router,
    dependencies=[Depends(get_current_user)]
)


scheduler.start()


def serialize_connection(connection: Connection) -> dict:
    return {
        "id": connection.id,
        "nombre": connection.nombre,
        "motor": connection.motor,
        "host": connection.host,
        "port": connection.port,
        "database_name": connection.database_name,
        "user_name": connection.user_name,
        "status": connection.status,
        "created_at": connection.created_at,
        "password_saved": bool(connection.encrypted_password),
    }


def classify_query(duration_ms: int):
    if duration_ms < 100:
        return "Fast"

    if duration_ms <= 500:
        return "Medium"

    if duration_ms <= 2000:
        return "Slow"

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

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc)
        }


@app.post("/connections")
def create_connection(
    connection: ConnectionCreate,
    validate_connection: bool = Query(
        True,
        description="Si es true, prueba la conexión real antes de registrar el motor."
    ),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    connection_test = None
    status_value = "PENDING"

    if validate_connection:
        connection_test = test_database_connection(
            motor=connection.motor,
            host=connection.host,
            port=connection.port,
            database_name=connection.database_name,
            user_name=connection.user_name,
            password=connection.password,
        )

        if connection_test.get("status") != "connected":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "No se registró la conexión porque la prueba real falló.",
                    "connection_test": connection_test
                }
            )

        status_value = "ONLINE"
    else:
        status_value = "UNKNOWN"

    try:
        new_connection = Connection(
            nombre=connection.nombre,
            motor=connection.motor,
            host=connection.host,
            port=connection.port,
            database_name=connection.database_name,
            user_name=connection.user_name,
            encrypted_password=encrypt_password(connection.password),
            status=status_value
        )

        db.add(new_connection)
        db.commit()
        db.refresh(new_connection)

        return {
            "message": "Motor registrado correctamente con credenciales cifradas.",
            "connection": serialize_connection(new_connection),
            "connection_test": connection_test
        }

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo guardar la conexión: {str(exc)}"
        ) from exc


@app.post("/connections/test")
def test_connection_direct(
    connection: ConnectionCreate,
    current_user=Depends(get_current_user)
):
    return test_database_connection(
        motor=connection.motor,
        host=connection.host,
        port=connection.port,
        database_name=connection.database_name,
        user_name=connection.user_name,
        password=connection.password,
    )


@app.post("/connections/{connection_id}/test")
def test_saved_connection(
    connection_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    saved_connection = db.query(Connection).filter(
        Connection.id == connection_id
    ).first()

    if not saved_connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Motor no encontrado"
        )

    try:
        plain_password = decrypt_password(saved_connection.encrypted_password)

    except ValueError as exc:
        saved_connection.status = "ERROR"
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        ) from exc

    result = test_database_connection(
        motor=saved_connection.motor,
        host=saved_connection.host,
        port=saved_connection.port,
        database_name=saved_connection.database_name,
        user_name=saved_connection.user_name,
        password=plain_password,
    )

    saved_connection.status = "ONLINE" if result.get("status") == "connected" else "ERROR"
    db.commit()
    db.refresh(saved_connection)

    return {
        "connection": serialize_connection(saved_connection),
        "connection_test": result
    }


@app.get("/connections")
def get_connections(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    connections = db.query(Connection).order_by(
        Connection.id.asc()
    ).all()

    return [
        serialize_connection(connection)
        for connection in connections
    ]


@app.get("/connections/databases")
def get_connection_databases(
    motor: str | None = Query(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Connection)

    if motor and motor != "Todos":
        query = query.filter(Connection.motor == motor)

    connections = query.order_by(
        Connection.motor.asc(),
        Connection.database_name.asc()
    ).all()

    return [
        {
            "connection_id": connection.id,
            "id": connection.id,
            "nombre": connection.nombre,
            "motor": connection.motor,
            "host": connection.host,
            "port": connection.port,
            "database_name": connection.database_name,
            "user_name": connection.user_name,
            "status": connection.status
        }
        for connection in connections
    ]


@app.delete("/connections/{connection_id}")
def delete_connection(
    connection_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    saved_connection = db.query(Connection).filter(
        Connection.id == connection_id
    ).first()

    if not saved_connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Motor no encontrado"
        )

    try:
        deleted_metrics = db.query(DBMetric).filter(
            DBMetric.connection_id == connection_id
        ).delete(
            synchronize_session=False
        )

        deleted_queries = db.query(QueryLog).filter(
            QueryLog.connection_id == connection_id
        ).delete(
            synchronize_session=False
        )

        connection_name = saved_connection.nombre

        db.delete(saved_connection)
        db.commit()

        return {
            "message": "Conexión eliminada correctamente.",
            "connection_id": connection_id,
            "connection_name": connection_name,
            "deleted_related_records": {
                "metrics": deleted_metrics,
                "query_logs": deleted_queries
            }
        }

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo eliminar la conexión: {str(exc)}"
        ) from exc


@app.get("/metrics")
def get_metrics(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    metrics = db.query(DBMetric).all()
    return metrics


@app.get("/health-summary")
def health_summary(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total_connections = db.query(Connection).count()
    total_metrics = db.query(DBMetric).count()

    latest_metric = db.query(DBMetric).order_by(
        DBMetric.capture_time.desc()
    ).first()

    return {
        "registered_engines": total_connections,
        "captured_metrics": total_metrics,
        "latest_cpu": latest_metric.cpu if latest_metric else None,
        "latest_memory": latest_metric.memory if latest_metric else None,
        "latest_disk_usage": latest_metric.disk_usage if latest_metric else None,
        "status": "monitoring_active"
    }


@app.get("/jobs/audit")
def get_job_audit(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(JobAudit).order_by(
        JobAudit.start_time.desc()
    ).limit(100).all()


@app.post("/queries")
def create_query_log(
    query: QueryLogCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
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

    return {
        "message": "Consulta registrada correctamente",
        "classification": new_query.classification,
        "duration_ms": new_query.duration_ms
    }


@app.get("/queries")
def get_query_logs(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    queries = db.query(QueryLog).all()
    return queries


@app.post("/login")
def login(user: LoginData):
    db: Session = SessionLocal()

    try:
        existing_user = db.query(User).filter(
            User.username == user.username
        ).first()

        if not existing_user:
            demo_user = User(
                username="admin",
                password="admin123"
            )

            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)

            existing_user = demo_user

        if existing_user.password != user.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )

        token = create_access_token(
            {
                "sub": existing_user.username
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer"
        }

    finally:
        db.close()


@app.post("/token")
def token_login(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    db: Session = SessionLocal()

    try:
        existing_user = db.query(User).filter(
            User.username == form_data.username
        ).first()

        if not existing_user:
            demo_user = User(
                username="admin",
                password="admin123"
            )

            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)

            existing_user = demo_user

        if existing_user.password != form_data.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
                headers={
                    "WWW-Authenticate": "Bearer"
                }
            )

        token = create_access_token(
            {
                "sub": existing_user.username
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer"
        }

    finally:
        db.close()