import os
import smtplib

from email.message import EmailMessage
from fastapi import APIRouter

from app.database import SessionLocal
from app.models import (
    AlertLog,
    AlertRule,
    DBMetric,
    Connection,
    BackupHistory,
    ReplicationStatus
)


router = APIRouter(
    prefix="/alerts",
    tags=["Alert Engine"]
)


DEFAULT_RULES = [
    {
        "rule_name": "CPU mayor a 85%",
        "metric_name": "cpu",
        "operator": ">",
        "threshold": 85,
        "severity": "Warning",
        "action": "Correo electrónico"
    },
    {
        "rule_name": "Deadlocks mayores a 3",
        "metric_name": "deadlocks",
        "operator": ">",
        "threshold": 3,
        "severity": "Critical",
        "action": "Alerta crítica en dashboard"
    },
    {
        "rule_name": "Backup fallido",
        "metric_name": "backup_failed",
        "operator": "==",
        "threshold": 1,
        "severity": "Critical",
        "action": "Alarma roja + correo"
    },
    {
        "rule_name": "Lag de replicación mayor a 10 segundos",
        "metric_name": "replication_lag",
        "operator": ">",
        "threshold": 10,
        "severity": "Warning",
        "action": "Notificación en dashboard"
    },
    {
        "rule_name": "Disco mayor a 90%",
        "metric_name": "disk_usage",
        "operator": ">",
        "threshold": 90,
        "severity": "Critical",
        "action": "Correo + alerta visual"
    },
    {
        "rule_name": "Conexiones mayores al umbral",
        "metric_name": "connections",
        "operator": ">",
        "threshold": 80,
        "severity": "Warning",
        "action": "Notificación automática"
    }
]


def send_alert_email(condition, engine, severity, action):

    email_enabled = os.getenv(
        "ALERT_EMAIL_ENABLED",
        "false"
    ).lower()

    if email_enabled != "true":
        return

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_to = os.getenv("ALERT_EMAIL_TO")

    if not smtp_host or not smtp_user or not smtp_password or not email_to:
        return

    message = EmailMessage()

    message["Subject"] = f"DataOps Alert - {severity}"
    message["From"] = smtp_user
    message["To"] = email_to

    message.set_content(
        f"Se generó una alerta en DataOps Control Center.\n\n"
        f"Condición: {condition}\n"
        f"Motor afectado: {engine}\n"
        f"Severidad: {severity}\n"
        f"Acción configurada: {action}\n"
        f"Estado: PENDING\n"
    )

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(
            smtp_user,
            smtp_password
        )
        server.send_message(message)


def ensure_default_rules(db):

    existing_rules = db.query(
        AlertRule
    ).count()

    if existing_rules > 0:
        return

    for rule in DEFAULT_RULES:

        new_rule = AlertRule(
            rule_name=rule["rule_name"],
            metric_name=rule["metric_name"],
            operator=rule["operator"],
            threshold=rule["threshold"],
            severity=rule["severity"],
            action=rule["action"],
            enabled=True
        )

        db.add(new_rule)

    db.commit()


def create_alert(db, condition, engine, severity, action):

    existing_pending = db.query(
        AlertLog
    ).filter(
        AlertLog.condition_triggered == condition,
        AlertLog.affected_engine == engine,
        AlertLog.severity == severity,
        AlertLog.resolution_status == "PENDING"
    ).first()

    if existing_pending:
        return None

    alert = AlertLog(
        condition_triggered=condition,
        affected_engine=engine,
        severity=severity,
        action=action,
        resolution_status="PENDING"
    )

    db.add(alert)

    if "correo" in action.lower():
        send_alert_email(
            condition,
            engine,
            severity,
            action
        )

    return {
        "condition_triggered": condition,
        "affected_engine": engine,
        "severity": severity,
        "action": action,
        "resolution_status": "PENDING"
    }


def evaluate_alerts_internal():

    db = SessionLocal()

    alerts_created = []

    try:

        ensure_default_rules(db)

        rules = db.query(
            AlertRule
        ).filter(
            AlertRule.enabled == True
        ).all()

        latest_metrics = db.query(
            DBMetric,
            Connection
        ).join(
            Connection,
            DBMetric.connection_id == Connection.id
        ).order_by(
            DBMetric.capture_time.desc()
        ).limit(30).all()

        for metric, connection in latest_metrics:

            for rule in rules:

                if rule.metric_name == "cpu" and metric.cpu > rule.threshold:

                    alert = create_alert(
                        db,
                        f"CPU > {rule.threshold}%",
                        connection.nombre,
                        rule.severity,
                        rule.action
                    )

                    if alert:
                        alerts_created.append(alert)

                if rule.metric_name == "deadlocks" and metric.deadlocks > rule.threshold:

                    alert = create_alert(
                        db,
                        f"Deadlocks > {rule.threshold}",
                        connection.nombre,
                        rule.severity,
                        rule.action
                    )

                    if alert:
                        alerts_created.append(alert)

                if rule.metric_name == "disk_usage" and metric.disk_usage > rule.threshold:

                    alert = create_alert(
                        db,
                        f"Disco > {rule.threshold}%",
                        connection.nombre,
                        rule.severity,
                        rule.action
                    )

                    if alert:
                        alerts_created.append(alert)

                if rule.metric_name == "connections" and metric.connections > rule.threshold:

                    alert = create_alert(
                        db,
                        f"Conexiones > {rule.threshold}",
                        connection.nombre,
                        rule.severity,
                        rule.action
                    )

                    if alert:
                        alerts_created.append(alert)

        latest_replication = db.query(
            ReplicationStatus
        ).order_by(
            ReplicationStatus.created_at.desc()
        ).first()

        for rule in rules:

            if (
                rule.metric_name == "replication_lag"
                and latest_replication
                and latest_replication.replication_lag > rule.threshold
            ):

                alert = create_alert(
                    db,
                    f"Lag replicación > {rule.threshold} segundos",
                    "Replica DB",
                    rule.severity,
                    rule.action
                )

                if alert:
                    alerts_created.append(alert)

            if rule.metric_name == "backup_failed":

                latest_backup = db.query(
                    BackupHistory
                ).order_by(
                    BackupHistory.created_at.desc()
                ).first()

                if (
                    not latest_backup
                    or not latest_backup.cloud_url
                    or latest_backup.backup_type == "FAILED"
                ):

                    alert = create_alert(
                        db,
                        "Backup fallido o sin URL remota",
                        "Backup Service",
                        rule.severity,
                        rule.action
                    )

                    if alert:
                        alerts_created.append(alert)

        db.commit()

        return alerts_created

    finally:

        db.close()


@router.post("/init-rules")
def init_alert_rules():

    db = SessionLocal()

    try:

        ensure_default_rules(db)

        rules_count = db.query(
            AlertRule
        ).count()

        return {
            "message": "Alert rules configured",
            "rules_count": rules_count
        }

    finally:

        db.close()


@router.get("/rules")
def get_alert_rules():

    db = SessionLocal()

    rules = db.query(
        AlertRule
    ).all()

    db.close()

    return rules


@router.put("/rules/{rule_id}")
def update_alert_rule(
    rule_id: int,
    threshold: float,
    enabled: bool
):

    db = SessionLocal()

    rule = db.query(
        AlertRule
    ).filter(
        AlertRule.id == rule_id
    ).first()

    if not rule:

        db.close()

        return {
            "error": "Rule not found"
        }

    rule.threshold = threshold
    rule.enabled = enabled

    db.commit()
    db.refresh(rule)

    db.close()

    return {
        "message": "Alert rule updated without redeploy",
        "rule": {
            "id": rule.id,
            "rule_name": rule.rule_name,
            "metric_name": rule.metric_name,
            "threshold": rule.threshold,
            "enabled": rule.enabled,
            "severity": rule.severity,
            "action": rule.action
        }
    }


@router.post("/evaluate")
def evaluate_alerts():

    alerts_created = evaluate_alerts_internal()

    return {
        "message": "Alert evaluation completed",
        "alerts_created": len(alerts_created),
        "alerts": alerts_created
    }


@router.get("/logs")
def get_alert_logs():

    db = SessionLocal()

    logs = db.query(
        AlertLog
    ).order_by(
        AlertLog.created_at.desc()
    ).limit(100).all()

    db.close()

    return logs


@router.put("/resolve/{alert_id}")
def resolve_alert(alert_id: int):

    db = SessionLocal()

    alert = db.query(
        AlertLog
    ).filter(
        AlertLog.id == alert_id
    ).first()

    if not alert:

        db.close()

        return {
            "error": "Alert not found"
        }

    alert.resolution_status = "RESOLVED"

    db.commit()
    db.refresh(alert)

    db.close()

    return {
        "message": "Alert resolved",
        "alert": {
            "id": alert.id,
            "condition_triggered": alert.condition_triggered,
            "affected_engine": alert.affected_engine,
            "severity": alert.severity,
            "action": alert.action,
            "resolution_status": alert.resolution_status,
            "created_at": alert.created_at
        }
    }