from pydantic import BaseModel, Field
from typing import Literal

class ConnectionCreate(BaseModel):
    nombre: str = Field(..., min_length=3)
    motor: Literal["PostgreSQL", "SQL Server", "Oracle"]
    host: str = Field(..., min_length=3)
    port: int = Field(..., gt=0)
    database_name: str = Field(..., min_length=2)
    user_name: str = Field(..., min_length=2)
    password: str = Field(..., min_length=4)