from fastapi import APIRouter
from app.api.v1.endpoints import metrics, users

api_router = APIRouter()
api_router.include_router(metrics.router)
api_router.include_router(users.router)
