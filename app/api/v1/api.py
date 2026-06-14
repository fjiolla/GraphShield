from fastapi import APIRouter
from app.api.v1.endpoints import audit
from app.api.v1.endpoints import struct_audit_api
from app.api.v1.endpoints import graph_audit    
from app.api.v1.endpoints import struct_model_audit_api
from app.api.v1.endpoints import graph_model_audit
from app.api.v1.endpoints import system
from app.api.v1.endpoints import chat
from app.api.v1.endpoints import demo
from app.api.v1.endpoints import demo_files
from app.api.v1.endpoints import export


api_router = APIRouter()
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(struct_audit_api.router, prefix="/struct-audit", tags=["struct-audit"])
api_router.include_router(graph_audit.router , prefix="/graph" , tags=["graphs-audit"])
api_router.include_router(struct_model_audit_api.router, prefix="/struct-model-audit", tags=["struct-model-audit"])
api_router.include_router(graph_model_audit.router, prefix="/graph-model-audit", tags=["graph-model-audit"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(demo.router, prefix="/demo", tags=["demo"])
api_router.include_router(demo_files.router, prefix="/demo-files", tags=["demo-files"])
api_router.include_router(export.router, prefix="/export", tags=["export"])

