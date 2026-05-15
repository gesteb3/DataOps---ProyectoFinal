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
    
class QueryLogCreate(BaseModel):
    connection_id: int = Field(..., gt=0)
    query_text: str = Field(..., min_length=5)
    duration_ms: int = Field(..., ge=0)
    rows_returned: int = Field(..., ge=0)
    index_used: Literal["YES", "NO"]
    execution_plan: str | None = None