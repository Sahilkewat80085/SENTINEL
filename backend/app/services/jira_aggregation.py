from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException
from app.core.logging import logger
from app.core.result import ServiceResult
from app.repositories import repository_repo
from app.repositories.jira_repo import jira_repo
from app.schemas.jira import JiraDetail, JiraSummary, JiraTimelineItem


class JiraAggregationService:
    """Service to handle Jira status classification and timeline aggregations."""

    def classify_status(self, last_updated: datetime) -> str:
        """Determines the active status of a Jira ticket based on its last commit timestamp.

        ACTIVE: last updated within 7 days
        STALE: 8-30 days
        DORMANT: 31-90 days
        ARCHIVED: >90 days
        """
        # Ensure timezone-aware comparisons
        now = datetime.now(timezone.utc)

        # Normalize last_updated to be timezone-aware (matching PostgreSQL timestamptz)
        if last_updated.tzinfo is None:
            last_updated = last_updated.replace(tzinfo=timezone.utc)

        delta = now - last_updated
        days = delta.days

        if days <= 7:
            return "ACTIVE"
        elif days <= 30:
            return "STALE"
        elif days <= 90:
            return "DORMANT"
        else:
            return "ARCHIVED"

    async def get_jira_list(
        self,
        db: AsyncSession,
        *,
        repository_id: Optional = None, # Wait, import Optional if not done
        search: Optional = None,
        skip: int = 0,
        limit: int = 50,
    ) -> ServiceResult[tuple[list[JiraSummary], int]]:
        """Fetch paginated lists of Jira summaries, computing their lifecycles."""
        try:
            summaries, total = await jira_repo.get_jira_summaries(
                db, repository_id=repository_id, search=search, skip=skip, limit=limit
            )

            # Apply classification on rows
            classified_summaries = []
            for s in summaries:
                status = self.classify_status(s["last_updated"])
                classified_summaries.append(
                    JiraSummary(
                        jira_id=s["jira_id"],
                        repository_id=s["repository_id"],
                        commit_count=s["commit_count"],
                        author_count=s["author_count"],
                        first_seen=s["first_seen"],
                        last_updated=s["last_updated"],
                        touched_folders=s["touched_folders"],
                        folder_count=s["folder_count"],
                        status=status,
                    )
                )

            return ServiceResult.success((classified_summaries, total))
        except Exception as e:
            logger.exception("Failed to retrieve Jira summaries list", error=str(e))
            from app.core.exceptions import DatabaseException
            return ServiceResult.failure(DatabaseException(f"Error fetching Jira summaries: {e}"))

    async def get_jira_detail(
        self, db: AsyncSession, jira_id: str, repository_id: Any
    ) -> ServiceResult[JiraDetail]:
        """Collects the timeline and summary details for a specific ticket key."""
        # Check repo config existence
        repo = await repository_repo.get(db, repository_id)
        if not repo:
            return ServiceResult.failure(EntityNotFoundException("Repository", repository_id))

        # We query the summary list filtered by repository & exact Jira key
        summaries, _ = await jira_repo.get_jira_summaries(
            db, repository_id=repository_id, search=jira_id, skip=0, limit=1
        )

        # Verify if ticket is found in database
        target_summary = None
        for s in summaries:
            if s["jira_id"].upper() == jira_id.upper():
                target_summary = s
                break

        if not target_summary:
            return ServiceResult.failure(EntityNotFoundException("JiraTicket", jira_id))

        # Get chronological commit timeline
        raw_timeline = await jira_repo.get_jira_timeline(db, jira_id, repository_id)

        timeline_items = []
        for t in raw_timeline:
            timeline_items.append(
                JiraTimelineItem(
                    sha=t["sha"],
                    message=t["message"],
                    commit_date=t["commit_date"],
                    author_name=t["author_name"],
                    author_email=t["author_email"],
                    folders=t["folders"],
                    files_count=t["files_count"],
                )
            )

        status = self.classify_status(target_summary["last_updated"])
        summary_obj = JiraSummary(
            jira_id=target_summary["jira_id"],
            repository_id=target_summary["repository_id"],
            commit_count=target_summary["commit_count"],
            author_count=target_summary["author_count"],
            first_seen=target_summary["first_seen"],
            last_updated=target_summary["last_updated"],
            touched_folders=target_summary["touched_folders"],
            folder_count=target_summary["folder_count"],
            status=status,
        )

        detail = JiraDetail(summary=summary_obj, timeline=timeline_items)
        return ServiceResult.success(detail)
