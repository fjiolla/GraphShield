from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ConnectionInfo(BaseModel):
    groq_status: str
    snowflake_status: str

@router.get("/status", response_model=ConnectionInfo)
async def get_connection_status():
    return {
        "groq_status": "Connected",
        "snowflake_status": "Not Configured"
    }
