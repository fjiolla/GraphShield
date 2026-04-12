from fastapi import APIRouter
from app.api.v1.endpoints import audit
from app.api.v1.endpoints import struct_audit_api

api_router = APIRouter()
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(struct_audit_api.router, prefix="/struct-audit", tags=["struct-audit"])