from fastapi import APIRouter

from app.api.v1.commits import router as commits_router
from app.api.v1.repositories import router as repositories_router
from app.api.v1.jiras import router as jiras_router
from app.api.v1.coverage import router as coverage_router
from app.api.v1.content import router as content_router
from app.api.v1.delays import router as delays_router
from app.api.v1.folders import router as folders_router
from app.api.v1.violations import router as violations_router

api_router = APIRouter()

# Mount endpoints
api_router.include_router(repositories_router, prefix="/repositories", tags=["Repositories"])
api_router.include_router(commits_router, prefix="/commits", tags=["Commits"])
api_router.include_router(jiras_router, prefix="/jiras", tags=["Jiras"])
api_router.include_router(coverage_router, prefix="/coverage", tags=["Coverage"])
api_router.include_router(content_router, prefix="/content", tags=["Content Verification"])
api_router.include_router(delays_router, prefix="/delays", tags=["Merge Delay Analytics"])
api_router.include_router(folders_router, prefix="/folders", tags=["Folder Health"])
api_router.include_router(violations_router, prefix="/violations", tags=["Exception Detection"])
