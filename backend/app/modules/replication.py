import random

from fastapi import APIRouter, HTTPException

from app.database import SessionLocal
from app.models import ReplicationStatus
from app.services.replication_lag_service import (
    LAG_SCENARIOS,
    get_lag_scenario,
    measure_postgres_replication_lag,
)


router = APIRouter(
    prefix="/replication",
    tags=["Replication"]
)


def save_replication_status(scenario: str, lag_seconds: float, status: str):
    db = SessionLocal()

    replication = ReplicationStatus(
        scenario=scenario,
        replication_lag=int(round(lag_seconds)),
        status=status
    )

    db.add(replication)
    db.commit()
    db.refresh(replication)
    db.close()

    return replication


@router.post("/simulate")
def simulate_replication():
    scenario = random.choice(list(LAG_SCENARIOS.values()))

    replication = save_replication_status(
        scenario=scenario["scenario"],
        lag_seconds=scenario["lag_seconds"],
        status=scenario["status"]
    )

    return {
        "scenario": replication.scenario,
        "lag_seconds": replication.replication_lag,
        "status": replication.status,
        "source": "SIMULATED_RANDOM"
    }


@router.post("/simulate/{level}")
def simulate_replication_by_level(level: str):
    try:
        scenario = get_lag_scenario(level)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    replication = save_replication_status(
        scenario=scenario["scenario"],
        lag_seconds=scenario["lag_seconds"],
        status=scenario["status"]
    )

    return {
        "scenario": replication.scenario,
        "lag_seconds": replication.replication_lag,
        "status": replication.status,
        "source": "SIMULATED_CONTROLLED",
        "cap_note": (
            "En CAP, al priorizar disponibilidad y tolerancia a particiones, "
            "la consistencia puede ser eventual; por eso el lag representa "
            "el tiempo en que la réplica tarda en reflejar los cambios del primario."
        )
    }


@router.get("/measure-real")
def measure_real_replication_lag():
    try:
        result = measure_postgres_replication_lag()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo medir el lag real de la réplica PostgreSQL: {str(exc)}"
        ) from exc

    replication = save_replication_status(
        scenario=result["scenario"],
        lag_seconds=result["lag_seconds"],
        status=result["status"]
    )

    return {
        "scenario": replication.scenario,
        "lag_seconds": result["lag_seconds"],
        "status": replication.status,
        "source": result["source"]
    }


@router.get("/status")
def get_replication_status():
    db = SessionLocal()

    data = db.query(
        ReplicationStatus
    ).order_by(
        ReplicationStatus.created_at.desc()
    ).all()

    db.close()

    return data
