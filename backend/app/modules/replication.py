import random

from fastapi import APIRouter

from app.database import SessionLocal
from app.models import ReplicationStatus


router = APIRouter(
    prefix="/replication",
    tags=["Replication"]
)


@router.post("/simulate")
def simulate_replication():

    db = SessionLocal()

    scenarios = [
        ("Carga normal", 2),
        ("Carga media", 5),
        ("Carga alta", 20)
    ]

    scenario = random.choice(scenarios)
    lag = scenario[1]

    if lag <= 2:
        status = "Aceptable"
    elif lag <= 5:
        status = "Advertencia"
    else:
        status = "Crítico"

    replication = ReplicationStatus(
        scenario=scenario[0],
        replication_lag=lag,
        status=status
    )

    db.add(replication)
    db.commit()
    db.close()

    return {
        "scenario": scenario[0],
        "lag_seconds": lag,
        "status": status
    }


@router.get("/status")
def get_replication_status():

    db = SessionLocal()

    data = db.query(
        ReplicationStatus
    ).all()

    db.close()

    return data