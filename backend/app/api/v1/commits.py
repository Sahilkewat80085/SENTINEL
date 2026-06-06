from typing import Any, List, Optional
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.core.exceptions import EntityNotFoundException
from app.models.commit import Commit
from app.models.user import User
from app.repositories.commit_repo import commit_repo
from app.schemas.commit import CommitDetailResponse, CommitResponse
from app.schemas.common import MetaData, ResponseEnvelope

router = APIRouter()


@router.get("", response_model=ResponseEnvelope[List[CommitResponse]])
async def list_commits(
    repository_id: Optional[uuid.UUID] = Query(None, description="Filter by repository UUID"),
    branch: Optional[str] = Query(None, description="Filter by branch name"),
    folder: Optional[str] = Query(None, description="Filter by configuration folder name"),
    jira_id: Optional[str] = Query(None, description="Filter by Jira ticket ID"),
    search: Optional[str] = Query(None, description="Search commit message or SHA"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List audited commits with advanced pagination, search, and metadata filters."""
    skip = (page - 1) * page_size

    # Fetch paginated commits from repository (without loading files to save memory)
    # The count and pagination logic is handled inside commit_repo
    # Wait, we need to load the author relation to serialize CommitResponse
    # We can write a custom retrieval in commit_repo, or modify the query in commit_repo to use options.
    # Let's write the query with author selectinload.
    # Actually, we can fetch commits using selectinload inside this endpoint:
    query = select(Commit).options(selectinload(Commit.author))
    
    # We will replicate the filter logic or just use a query select
    # Let's check how commit_repo.get_paginated_commits is written. It returns list of Commit.
    # To avoid DetachedInstanceError, let's load authors in the repo query or do it here.
    # In commit_repo.py, the query was: `query = select(self.model)`.
    # Let's adjust commit_repo or retrieve it directly here with selectinload.
    # Direct retrieval with selectinload here is extremely safe:
    from app.models.commit_file import CommitFile
    from app.models.commit_jira import CommitJira
    from sqlalchemy import func

    stmt = select(Commit).options(selectinload(Commit.author))
    count_stmt = select(func.count(Commit.id))

    filters = []
    if repository_id:
        filters.append(Commit.repository_id == repository_id)
    if branch:
        filters.append(Commit.branch == branch)

    if folder:
        stmt = stmt.join(CommitFile).where(CommitFile.folder == folder)
        count_stmt = count_stmt.join(CommitFile).where(CommitFile.folder == folder)

    if jira_id:
        stmt = stmt.join(CommitJira).where(CommitJira.jira_id == jira_id)
        count_stmt = count_stmt.join(CommitJira).where(CommitJira.jira_id == jira_id)

    if search:
        search_filter = or_ = and_(
            (Commit.message.ilike(f"%{search}%") | Commit.sha.ilike(f"%{search}%"))
        )
        # Wait, using SQLAlchemy operators is cleaner:
        from sqlalchemy import or_
        filters.append(or_(Commit.message.ilike(f"%{search}%"), Commit.sha.ilike(f"%{search}%")))

    if filters:
        stmt = stmt.where(and_(*filters))
        count_stmt = count_stmt.where(and_(*filters))

    stmt = stmt.order_by(Commit.commit_date.desc()).offset(skip).limit(page_size)

    res = await db.execute(stmt)
    commits = list(res.scalars().all())

    count_res = await db.execute(count_stmt)
    total = count_res.scalar_one()

    has_next = total > (page * page_size)

    meta = MetaData(
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next
    )

    return ResponseEnvelope(success=True, data=commits, meta=meta)


@router.get("/{sha}", response_model=ResponseEnvelope[CommitDetailResponse])
async def get_commit(
    sha: str,
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch commit detail (including files and Jira linkages) by SHA."""
    stmt = (
        select(Commit)
        .options(
            selectinload(Commit.author),
            selectinload(Commit.files),
            selectinload(Commit.jiras),
        )
        .where(and_(Commit.sha == sha, Commit.repository_id == repository_id))
    )
    result = await db.execute(stmt)
    commit = result.scalar_one_or_none()
    if not commit:
        raise EntityNotFoundException("Commit", sha)

    # Flatten Jiras list in Response
    jiras_list = [j.jira_id for j in commit.jiras]

    # Map to schema details manually to avoid ORM circular references
    detail = CommitDetailResponse(
        id=commit.id,
        sha=commit.sha,
        repository_id=commit.repository_id,
        branch=commit.branch,
        message=commit.message,
        commit_date=commit.commit_date,
        ingested_at=commit.ingested_at,
        author=commit.author,
        files=commit.files,
        jiras=jiras_list
    )

    return ResponseEnvelope(success=True, data=detail)
