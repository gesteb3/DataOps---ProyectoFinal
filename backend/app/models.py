from sqlalchemy import Column,Integer,String,Float,DateTime,Boolean
from datetime import datetime
from app.database import Base
from sqlalchemy import ForeignKey, Float
from sqlalchemy.orm import relationship


class Connection(Base):
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    motor = Column(String(50), nullable=False)
    host = Column(String(100), nullable=False)
    port = Column(Integer, nullable=False)
    database_name = Column(String(100), nullable=False)
    user_name = Column(String(100), nullable=False)
    encrypted_password = Column(String(255), nullable=False)
    status = Column(String(50), default="UNKNOWN")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    
class DBMetric(Base):
    __tablename__ = "db_metrics"

    id = Column(Integer, primary_key=True)

    connection_id = Column(
        Integer,
        ForeignKey("connections.id")
    )

    cpu = Column(Float)
    memory = Column(Float)
    connections = Column(Integer)
    locks = Column(Integer)
    deadlocks = Column(Integer)
    disk_usage = Column(Float)

    capture_time = Column(
        DateTime,
        default=datetime.utcnow
    )
    
class QueryLog(Base):
    __tablename__ = "query_log"

    id = Column(Integer, primary_key=True)
    connection_id = Column(Integer, ForeignKey("connections.id"))

    query_text = Column(String, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    rows_returned = Column(Integer, default=0)
    index_used = Column(String(10), default="NO")
    execution_plan = Column(String, nullable=True)
    classification = Column(String(20), nullable=False)

    capture_time = Column(
        DateTime,
        default=datetime.utcnow
    )

class BackupHistory(Base):
    __tablename__ = "backup_history"

    id = Column(Integer, primary_key=True, index=True)
    backup_type = Column(String)
    file_name = Column(String)
    size_mb = Column(Float)
    duration_seconds = Column(Float)
    restore_point = Column(String)
    snapshot_name = Column(String)
    cloud_url = Column(String)
    hash_value = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String,
        unique=True
    )

    password = Column(
        String
    )

    is_active = Column(
        Boolean,
        default=True
    )

class ReplicationStatus(Base):
    __tablename__ = "replication_status"

    id = Column(Integer, primary_key=True, index=True)
    scenario = Column(String)
    replication_lag = Column(Integer)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class CacheMetric(Base):
    __tablename__ = "cache_metrics"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    query_key = Column(String)

    cache_status = Column(String)

    response_time_ms = Column(Float)

    ttl_seconds = Column(Integer)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )