from sqlalchemy import Column, Integer, String, DateTime
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