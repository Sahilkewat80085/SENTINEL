from fastapi import APIRouter

from app.api.v1.commits import router as commits_router
from app.api.v1.repositories import router as repositories_router
from app.api.v1.jiras import router as jiras_router

api_router = APIRouter()

# Mount endpoints
api_router.include_router(repositories_router, prefix="/repositories", tags=["Repositories"])
api_router.include_router(commits_router, prefix="/commits", tags=["Commits"])
api_router.include_router(jiras_router, prefix="/jiras", tags=["Jiras"])
