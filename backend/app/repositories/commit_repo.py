from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.models.commit import Commit
from app.models.author import Author
from app.models.commit_file import CommitFile
from app.models.commit_jira import CommitJira
from app.repositories.base import BaseRepository


class CommitRepository(BaseRepository[Commit]):
    """Repository class for commits with bulk insert capabilities and advanced filters."""

    def __init__(self) -> None:
        super().__init__(Commit)

    async def get_by_sha(self, db: AsyncSession, sha: str, repository_id: Any) -> Optional[Commit]:
        """Fetch a specific commit by SHA and repository context."""
        query = select(self.model).where(
            and_(self.model.sha == sha, self.model.repository_id == repository_id)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_commits_for_repository(
        self, db: AsyncSession, repository_id: Any, limit: int = 100
    ) -> List[Commit]:
        """Fetch recent commits for a specific repository up to a limit."""
        commits, _ = await self.get_paginated_commits(db, repository_id=repository_id, limit=limit)
        return commits

    async def get_paginated_commits(
        self,
        db: AsyncSession,
        *,
        repository_id: Optional[Any] = None,
        branch: Optional[str] = None,
        folder: Optional[str] = None,
        jira_id: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Commit], int]:
        """Query commits using customizable pagination and filters."""
        query = select(self.model)
        count_query = select(func.count(self.model.id))

        filters = []
        if repository_id:
            filters.append(self.model.repository_id == repository_id)
        if branch:
            filters.append(self.model.branch == branch)

        # Folder joins if needed
        if folder:
            # Check commit files folder
            query = query.join(CommitFile).where(CommitFile.folder == folder)
            count_query = count_query.join(CommitFile).where(CommitFile.folder == folder)

        # Jira joins if needed
        if jira_id:
            query = query.join(CommitJira).where(CommitJira.jira_id == jira_id)
            count_query = count_query.join(CommitJira).where(CommitJira.jira_id == jira_id)

        # Search term filters
        if search:
            search_filter = or_(
                self.model.message.ilike(f"%{search}%"),
                self.model.sha.ilike(f"%{search}%"),
            )
            filters.append(search_filter)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Order by newest commits
        query = query.order_by(self.model.commit_date.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        commits = list(result.scalars().all())

        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        return commits, total

    async def bulk_upsert_authors(self, db: AsyncSession, authors_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk inserts authors and maps their email address to author IDs.

        This uses PostgreSQL ON CONFLICT DO UPDATE to ensure all authors are created or updated.
        """
        if not authors_data:
            return {}

        email_to_id = {}

        # Chunk insertion to prevent query complexity issues
        for chunk in [authors_data[i : i + 200] for i in range(0, len(authors_data), 200)]:
            for author_val in chunk:
                stmt = (
                    insert(Author)
                    .values(
                        name=author_val["name"],
                        email=author_val["email"],
                        github_username=author_val.get("github_username"),
                    )
                    .on_conflict_do_update(
                        index_elements=["email"],
                        set_={
                            "name": author_val["name"],
                            "github_username": author_val.get("github_username") or Author.github_username,
                        },
                    )
                    .returning(Author.email, Author.id)
                )
                res = await db.execute(stmt)
                for email, auth_id in res.all():
                    email_to_id[email] = auth_id

        return email_to_id

    async def bulk_insert_commits_and_relations(
        self,
        db: AsyncSession,
        commits_data: List[Dict[str, Any]],
        files_data: List[Dict[str, Any]],
        jiras_data: List[Dict[str, Any]],
    ) -> List[Any]:
        """Bulk inserts commits, files, and Jira associations.

        Avoids duplicates by using PostgreSQL conflict resolution strategies.
        """
        if not commits_data:
            return []

        inserted_commit_ids = []

        # 1. Insert Commits
        for commit_val in commits_data:
            stmt = (
                insert(Commit)
                .values(
                    id=commit_val.get("id"),
                    sha=commit_val["sha"],
                    repository_id=commit_val["repository_id"],
                    author_id=commit_val["author_id"],
                    branch=commit_val.get("branch"),
                    message=commit_val["message"],
                    commit_date=commit_val["commit_date"],
                )
                .on_conflict_do_nothing(index_elements=["sha", "repository_id"])
                .returning(Commit.id)
            )
            res = await db.execute(stmt)
            inserted_val = res.scalar_one_or_none()
            if inserted_val:
                inserted_commit_ids.append(inserted_val)

        inserted_set = set(inserted_commit_ids)

        # 2. Insert Files (linked to commit_id)
        if files_data:
            for file_val in files_data:
                if file_val["commit_id"] not in inserted_set:
                    continue
                stmt = (
                    insert(CommitFile)
                    .values(
                        commit_id=file_val["commit_id"],
                        file_path=file_val["file_path"],
                        folder=file_val.get("folder"),
                        change_type=file_val["change_type"],
                        additions=file_val.get("additions", 0),
                        deletions=file_val.get("deletions", 0),
                    )
                    .on_conflict_do_nothing(index_elements=["commit_id", "file_path"])
                )
                await db.execute(stmt)

        # 3. Insert Jira Mappings (linked to commit_id)
        if jiras_data:
            for jira_val in jiras_data:
                if jira_val["commit_id"] not in inserted_set:
                    continue
                stmt = (
                    insert(CommitJira)
                    .values(
                        commit_id=jira_val["commit_id"],
                        jira_id=jira_val["jira_id"],
                    )
                    .on_conflict_do_nothing(index_elements=["commit_id", "jira_id"])
                )
                await db.execute(stmt)

        return inserted_commit_ids


# Singleton instance
commit_repo = CommitRepository()
