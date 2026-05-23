import json
import time

import redis
from fastapi import APIRouter

from app.config import settings
from app.database import SessionLocal
from app.models import CacheMetric


router = APIRouter(
    prefix="/cache",
    tags=["Cache Redis"]
)


redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2
)

CACHE_TTL_SECONDS = settings.CACHE_TTL_SECONDS

def generate_simulated_data(query_key: str):
    return {
        "message": "Resultado generado desde base de datos simulada",
        "query": query_key,
        "records": [
            {"id": 1, "name": "DataOps metric"},
            {"id": 2, "name": "Backup history"},
            {"id": 3, "name": "Replication status"}
        ]
    }


def save_cache_metric(query_key, cache_status, response_time_ms):

    db = SessionLocal()

    metric = CacheMetric(
        query_key=query_key,
        cache_status=cache_status,
        response_time_ms=response_time_ms,
        ttl_seconds=CACHE_TTL_SECONDS
    )

    db.add(metric)
    db.commit()
    db.close()


@router.get("/query/{query_key}")
def cached_query(query_key: str):
    start = time.time()

    try:
        cached_data = redis_client.get(query_key)

        if cached_data:
            time.sleep(0.04)

            response_time = round(
                (time.time() - start) * 1000,
                2
            )

            save_cache_metric(
                query_key,
                "HIT",
                response_time
            )

            return {
                "query_key": query_key,
                "cache_status": "HIT",
                "response_time_ms": response_time,
                "redis_available": True,
                "data": json.loads(cached_data)
            }

        time.sleep(0.4)

        data = generate_simulated_data(query_key)

        redis_client.setex(
            query_key,
            CACHE_TTL_SECONDS,
            json.dumps(data)
        )

        response_time = round(
            (time.time() - start) * 1000,
            2
        )

        save_cache_metric(
            query_key,
            "MISS",
            response_time
        )

        return {
            "query_key": query_key,
            "cache_status": "MISS",
            "response_time_ms": response_time,
            "redis_available": True,
            "data": data
        }

    except redis.RedisError as e:
        time.sleep(0.4)

        data = generate_simulated_data(query_key)

        response_time = round(
            (time.time() - start) * 1000,
            2
        )

        save_cache_metric(
            query_key,
            "CACHE_ERROR",
            response_time
        )

        return {
            "query_key": query_key,
            "cache_status": "CACHE_ERROR",
            "response_time_ms": response_time,
            "redis_available": False,
            "warning": "Redis no respondió. Se usó fallback sin caché.",
            "error_detail": str(e),
            "data": data
        }

    time.sleep(0.4)

    data = {
        "message": "Resultado generado desde base de datos simulada",
        "query": query_key,
        "records": [
            {
                "id": 1,
                "name": "DataOps metric"
            },
            {
                "id": 2,
                "name": "Backup history"
            },
            {
                "id": 3,
                "name": "Replication status"
            }
        ]
    }

    redis_client.setex(
        query_key,
        CACHE_TTL_SECONDS,
        json.dumps(data)
    )

    response_time = round(
        (time.time() - start) * 1000,
        2
    )

    save_cache_metric(
        query_key,
        "MISS",
        response_time
    )

    return {
        "query_key": query_key,
        "cache_status": "MISS",
        "response_time_ms": response_time,
        "data": data
    }


@router.delete("/invalidate/{query_key}")
def invalidate_cache(query_key: str):

    redis_client.delete(query_key)

    return {
        "message": "Cache invalidated",
        "query_key": query_key
    }


@router.get("/metrics")
def get_cache_metrics():

    db = SessionLocal()

    data = db.query(
        CacheMetric
    ).all()

    db.close()

    return data


@router.get("/summary")
def cache_summary():

    db = SessionLocal()

    total = db.query(
        CacheMetric
    ).count()

    hits = db.query(
        CacheMetric
    ).filter(
        CacheMetric.cache_status == "HIT"
    ).count()

    misses = db.query(
        CacheMetric
    ).filter(
        CacheMetric.cache_status == "MISS"
    ).count()
    
    cache_errors = db.query(
        CacheMetric
    ).filter(
    CacheMetric.cache_status == "CACHE_ERROR"
    ).count()

    db.close()

    hit_rate = 0

    if total > 0:
        hit_rate = round(
            (hits / total) * 100,
            2
        )

    return {
        "total_requests": total,
        "cache_hits": hits,
        "cache_misses": misses,
        "hit_rate_percentage": hit_rate,
        "ttl_seconds": CACHE_TTL_SECONDS,
        "strategy": "TTL expiration and manual invalidation by event",
        "cache_errors": cache_errors
    }