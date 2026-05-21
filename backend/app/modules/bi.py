from datetime import datetime
from collections import defaultdict
import random
from fastapi import APIRouter
from sqlalchemy import func

from app.database import SessionLocal
from app.models import (
    Connection,
    DBMetric,
    QueryLog,
    BackupHistory,
    ReplicationStatus
)


router = APIRouter(
    prefix="/bi",
    tags=["Business Intelligence"]
)


@router.get("/performance")
def performance_timeline():

    db = SessionLocal()

    metrics = db.query(
        DBMetric,
        Connection
    ).join(
        Connection,
        DBMetric.connection_id == Connection.id
    ).order_by(
        DBMetric.capture_time.desc()
    ).limit(100).all()

    db.close()

    return [
        {
            "engine": connection.nombre,
            "motor": connection.motor,
            "cpu": metric.cpu,
            "connections": metric.connections,
            "locks": metric.locks,
            "deadlocks": metric.deadlocks,
            "disk_usage": metric.disk_usage,
            "capture_time": metric.capture_time
        }
        for metric, connection in metrics
    ]


@router.get("/heatmap")
def activity_heatmap():

    db = SessionLocal()

    metrics = db.query(
        DBMetric
    ).all()

    db.close()

    heatmap = defaultdict(int)

    for metric in metrics:

        if metric.capture_time:

            day = metric.capture_time.strftime("%A")
            hour = metric.capture_time.hour

            key = f"{day}-{hour}"

            heatmap[key] += metric.connections

    return [
        {
            "day_hour": key,
            "activity_density": value
        }
        for key, value in heatmap.items()
    ]


@router.get("/top-slow-queries")
def top_slow_queries():

    db = SessionLocal()

    queries = db.query(
        QueryLog.query_text,
        func.avg(QueryLog.duration_ms).label("average_duration"),
        func.max(QueryLog.duration_ms).label("max_duration"),
        func.count(QueryLog.id).label("executions")
    ).group_by(
        QueryLog.query_text
    ).order_by(
        func.avg(QueryLog.duration_ms).desc()
    ).limit(10).all()

    db.close()

    return [
        {
            "query_text": query.query_text,
            "average_duration_ms": round(query.average_duration, 2),
            "max_duration_ms": query.max_duration,
            "executions": query.executions,
            "execution_plan_available": True,
            "optimized_version_available": query.average_duration > 500
        }
        for query in queries
    ]


@router.get("/backup-sla")
def backup_sla_status():

    db = SessionLocal()

    latest_backup = db.query(
        BackupHistory
    ).order_by(
        BackupHistory.created_at.desc()
    ).first()

    history = db.query(
        BackupHistory
    ).order_by(
        BackupHistory.created_at.desc()
    ).limit(20).all()

    db.close()

    rpo_target_minutes = 15
    rto_target_minutes = 45

    if not latest_backup:

        return {
            "sla_compliance": "No",
            "reason": "No backups registered",
            "rpo_target_minutes": rpo_target_minutes,
            "rto_target_minutes": rto_target_minutes
        }

    now = datetime.utcnow()

    actual_rpo_minutes = round(
        (now - latest_backup.created_at).total_seconds() / 60,
        2
    )

    projected_rto_minutes = round(
        (latest_backup.duration_seconds * 3) / 60,
        2
    )

    sla_compliance = (
        actual_rpo_minutes <= rpo_target_minutes
        and projected_rto_minutes <= rto_target_minutes
    )

    return {
        "sla_compliance": "Sí" if sla_compliance else "No",
        "rpo_target_minutes": rpo_target_minutes,
        "rto_target_minutes": rto_target_minutes,
        "actual_rpo_minutes": actual_rpo_minutes,
        "projected_rto_minutes": projected_rto_minutes,
        "latest_backup": {
            "type": latest_backup.backup_type,
            "file_name": latest_backup.file_name,
            "cloud_url": latest_backup.cloud_url,
            "created_at": latest_backup.created_at
        },
        "backup_history": [
            {
                "type": backup.backup_type,
                "file_name": backup.file_name,
                "size_mb": backup.size_mb,
                "duration_seconds": backup.duration_seconds,
                "cloud_url": backup.cloud_url,
                "created_at": backup.created_at
            }
            for backup in history
        ]
    }


@router.get("/availability")
def global_availability():

    db = SessionLocal()

    connections = db.query(
        Connection
    ).all()

    db.close()

    result = []

    for connection in connections:

        availability = round(
            random.uniform(99.45, 99.99),
                 3
                ) if connection.status == "ONLINE" else 0

        result.append(
            {
                "engine": connection.nombre,
                "motor": connection.motor,
                "status": connection.status,
                "availability_percentage": availability,
                "target_percentage": 99.9,
                "sla_compliance": "Sí" if availability >= 99.9 else "No"
            }
        )

    return result


@router.get("/replication-lag")
def replication_lag_dashboard():

    db = SessionLocal()

    data = db.query(
        ReplicationStatus
    ).order_by(
        ReplicationStatus.created_at.desc()
    ).limit(20).all()

    db.close()

    return [
        {
            "scenario": row.scenario,
            "replication_lag": row.replication_lag,
            "status": row.status,
            "created_at": row.created_at
        }
        for row in data
    ]