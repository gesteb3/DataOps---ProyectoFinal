from sqlalchemy import Column,Integer,String,Float,DateTime
from datetime import datetime
from app.database import Base


class BackupHistory(Base):
    __tablename__="backup_history"

    id=Column(Integer,primary_key=True,index=True)

    backup_type=Column(String)
    file_name=Column(String)

    size_mb=Column(Float)

    duration_seconds=Column(Float)

    restore_point=Column(String)

    snapshot_name=Column(String)

    cloud_url=Column(String)

    hash_value=Column(String)

    created_at=Column(
        DateTime,
        default=datetime.utcnow
    )