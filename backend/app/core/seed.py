"""
Database Seeding Script for SENTINEL.
Populates Postgres database with rich mock data for local testing and demonstration.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import date, timedelta

from sqlalchemy import select, text

from app.core.database import get_db_context
from app.core.security import get_password_hash
from app.models.author import Author
from app.models.repository import Repository
from app.models.snapshot import FolderHealthSnapshot, GovernanceSnapshot
from app.models.user import User
from app.services.content_verification import ContentVerificationService
from app.services.exception_detection import ExceptionDetectionService


async def seed_data():
    print("🛡 Seeding SENTINEL database with mock data...")

    async with get_db_context() as db:
        # 1. Seed admin user if it does not exist
        res = await db.execute(text("SELECT id FROM users WHERE username = 'admin'"))
        admin_user = res.scalar_one_or_none()
        if not admin_user:
            print("Creating administrator user 'admin'...")
            password_hash = get_password_hash("admin")
            db_admin = User(
                username="admin",
                email="admin@sentinel.local",
                password_hash=password_hash,
                role="admin",
                is_active=True
            )
            db.add(db_admin)
            await db.flush()

        # 2. Seed default repository
        res = await db.execute(text("SELECT id FROM repositories WHERE name = 'SENTINEL'"))
        repo_id = res.scalar_one_or_none()
        if not repo_id:
            print("Creating default 'SENTINEL' repository...")
            repo = Repository(
                id=uuid.UUID("7c3f3f3f-4f4f-4f4f-4f4f-4f4f4f4f4f4f"),
                name="SENTINEL",
                url="https://github.com/Sahilkewat80085/SENTINEL",
                default_branch="main",
                folders=["backend", "frontend", "nginx", "monitoring"],
                jira_patterns=["SEN-\\d+"],
                sync_mode="api",
                sync_interval=30,
                is_active=True
            )
            db.add(repo)
            await db.flush()
            repo_id = repo.id
        else:
            repo_id = uuid.UUID(str(repo_id))
            # Update url and folders if they exist
            stmt = select(Repository).where(Repository.id == repo_id)
            repo = (await db.execute(stmt)).scalar_one()
            repo.url = "https://github.com/Sahilkewat80085/SENTINEL"
            repo.folders = ["backend", "frontend", "nginx", "monitoring"]
            db.add(repo)
            await db.flush()

        # 3. Seed authors
        print("Seeding authors...")
        authors_data = [
            {"name": "Alice Smith", "email": "alice@sentinel.local", "github_username": "alice_git"},
            {"name": "Bob Jones", "email": "bob@sentinel.local", "github_username": "bob_git"},
            {"name": "Charlie Miller", "email": "charlie@sentinel.local", "github_username": "charlie_git"},
        ]

        author_objs = []
        for auth_data in authors_data:
            res = await db.execute(text("SELECT id FROM authors WHERE email = :email"), {"email": auth_data["email"]})
            auth_id = res.scalar_one_or_none()
            if not auth_id:
                author = Author(**auth_data)
                db.add(author)
                await db.flush()
                author_objs.append(author)
            else:
                # Retrieve existing author
                from app.models.author import Author as AuthorModel
                stmt = select(AuthorModel).where(AuthorModel.id == auth_id)
                author_objs.append((await db.execute(stmt)).scalar_one())

        # Clean existing mock commits/files/jiras/violations for the repo to allow fresh seeding
        await db.execute(text("DELETE FROM commit_files WHERE commit_id IN (SELECT id FROM commits WHERE repository_id = :repo_id)"), {"repo_id": repo_id})
        await db.execute(text("DELETE FROM commit_jiras WHERE commit_id IN (SELECT id FROM commits WHERE repository_id = :repo_id)"), {"repo_id": repo_id})
        await db.execute(text("DELETE FROM file_hashes WHERE repository_id = :repo_id"), {"repo_id": repo_id})
        await db.execute(text("DELETE FROM commits WHERE repository_id = :repo_id"), {"repo_id": repo_id})
        await db.execute(text("DELETE FROM rule_violations WHERE repository_id = :repo_id"), {"repo_id": repo_id})
        await db.execute(text("DELETE FROM governance_snapshots WHERE repository_id = :repo_id"), {"repo_id": repo_id})
        await db.execute(text("DELETE FROM folder_health_snapshots WHERE repository_id = :repo_id"), {"repo_id": repo_id})
        await db.commit()

        # 4. Sync real commits from public GitHub API
        print("Syncing real commits from public GitHub API...")
        from app.services.commit_collector import CommitCollectorService
        collector = CommitCollectorService()
        sync_res = await collector.sync_repository(db, repo_id)
        if sync_res.is_failure:
            print(f"GitHub Sync Failed: {sync_res.error}.")
        else:
            print(f"Synced successfully: {sync_res.value}")

        await db.commit()

        # 5. Refresh Materialized Views
        print("Refreshing materialized views...")
        await db.execute(text("REFRESH MATERIALIZED VIEW mv_jira_summary"))
        await db.execute(text("REFRESH MATERIALIZED VIEW mv_coverage_matrix"))
        await db.commit()

        # 6. Seed mock file hashes for content verification
        print("Scanning and seeding mock hashes...")
        content_service = ContentVerificationService()
        await content_service.verify_repository_files(db, repo_id)

        # 7. Evaluate rules to detect violations
        print("Evaluating governance rules...")
        violation_service = ExceptionDetectionService()
        await violation_service.evaluate_rules(db, repo_id)

        # 8. Seed historical daily snapshots (30 days trend points)
        print("Seeding daily snapshots for historical graphs...")
        start_date = date.today() - timedelta(days=30)

        for i in range(31):
            snap_date = start_date + timedelta(days=i)
            progress_ratio = i / 30.0

            cov_pct = 70.0 + (progress_ratio * 15.0)  # 70% to 85%
            avg_delay = 8.5 - (progress_ratio * 3.5)  # 8.5 to 5.0 days
            crit_count = max(0, int(3 - (progress_ratio * 3)))
            health_avg = 72.0 + (progress_ratio * 18.0) # 72% to 90%

            snap = GovernanceSnapshot(
                repository_id=repo_id,
                snapshot_date=snap_date,
                total_jiras=15,
                total_commits=35 + i,
                overall_coverage_pct=round(cov_pct, 2),
                missing_merge_count=3 if i < 15 else 2,
                critical_violation_count=crit_count,
                avg_delay_days=round(avg_delay, 2),
                governance_score=round(health_avg, 2),
                metadata_info={
                    "high_violation_count": 2 if i < 20 else 1,
                    "medium_violation_count": 3,
                    "low_violation_count": 5
                }
            )
            db.add(snap)

            for folder in ["backend", "frontend", "nginx", "monitoring"]:
                if folder == "backend":
                    base_h = 95.0
                elif folder == "frontend":
                    base_h = 75.0 + (progress_ratio * 15.0)
                else:
                    base_h = 85.0 + (progress_ratio * 10.0)

                fsnap = FolderHealthSnapshot(
                    repository_id=repo_id,
                    snapshot_date=snap_date,
                    folder_name=folder,
                    health_score=round(base_h, 2),
                    coverage_score=round(base_h - 2.0, 2),
                    consistency_score=round(base_h + 1.0, 2),
                    timeliness_score=round(100.0 - (avg_delay * 3.0), 2),
                    completeness_score=100.0
                )
                db.add(fsnap)

        await db.commit()
        print("✅ Seeding complete! SENTINEL database is now fully populated with real repo commits.")


if __name__ == "__main__":
    asyncio.run(seed_data())
