from fastapi import APIRouter
from app.api.v1.endpoints import audit
from app.api.v1.endpoints import struct_audit_api
from app.api.v1.endpoints import graph_audit


api_router = APIRouter()
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(struct_audit_api.router, prefix="/struct-audit", tags=["struct-audit"])
api_router.include_router(graph_audit.router , prefix="/graph" , tags=["graphs-audit"])

