"""
Database Seeding Script for SENTINEL.
Populates Postgres database with rich mock data for local testing and demonstration.
"""
from __future__ import annotations

import asyncio
import uuid
import random
import hashlib
from datetime import datetime, date, timedelta, timezone

from sqlalchemy import text
from app.core.database import get_db_context
from app.core.security import get_password_hash
from app.models.repository import Repository
from app.models.author import Author
from app.models.commit import Commit
from app.models.commit_file import CommitFile
from app.models.commit_jira import CommitJira
from app.models.user import User
from app.models.snapshot import GovernanceSnapshot, FolderHealthSnapshot
from app.services.exception_detection import ExceptionDetectionService
from app.services.content_verification import ContentVerificationService


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
                url="mock://github.com/Sahilkewat80085/SENTINEL",
                default_branch="main",
                folders=["vanilla", "MET", "AMO"],
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
                res = await db.execute(text("SELECT * FROM authors WHERE id = :id"), {"id": auth_id})
                row = res.first()
                if row:
                    # fetch model object
                    from app.models.author import Author as AuthorModel
                    stmt = select(AuthorModel).where(AuthorModel.id == auth_id)
                    author_objs.append((await db.execute(stmt)).scalar_one())

        # Clean existing mock commits/files/jiras/violations for the repo to allow fresh seeding
        await db.execute(text("DELETE FROM commit_files WHERE commit_id IN (SELECT id FROM commits WHERE repository_id = :repo_id)"), {"repo_id": repo_id})
        await db.execute(text("DELETE FROM commit_jiras WHERE commit_id IN (SELECT id FROM commits WHERE repository_id = :repo_id)"), {"repo_id": repo_id})
        await db.execute(text("DELETE FROM commits WHERE repository_id = :repo_id"), {"repo_id": repo_id})
        await db.execute(text("DELETE FROM rule_violations WHERE repository_id = :repo_id"), {"repo_id": repo_id})
        await db.execute(text("DELETE FROM governance_snapshots WHERE repository_id = :repo_id"), {"repo_id": repo_id})
        await db.execute(text("DELETE FROM folder_health_snapshots WHERE repository_id = :repo_id"), {"repo_id": repo_id})
        await db.commit()

        # 4. Seed commits (30 days of commits history to build nice trends)
        print("Generating mock commit history...")
        now = datetime.now(timezone.utc)
        random.seed(42)
        
        # We will create 20 Jira tickets
        jiras = [f"SEN-{i}" for i in range(101, 121)]
        
        # Each Jira ticket will have:
        # - A commit in vanilla folder
        # - A commit in MET folder (90% probability, to create partial coverage)
        # - A commit in AMO folder (75% probability, to create missing merges)
        for idx, jira in enumerate(jiras):
            auth = random.choice(author_objs)
            base_date = now - timedelta(days=25 - (idx * 1.2))
            
            # Commit 1: Vanilla (Initial)
            sha1 = hashlib.sha1(f"{jira}-vanilla".encode()).hexdigest()
            c1 = Commit(
                sha=sha1,
                repository_id=repo_id,
                author_id=auth.id,
                branch="main",
                message=f"feat: implemented feature for {jira} in vanilla layout",
                commit_date=base_date
            )
            db.add(c1)
            await db.flush()
            
            db.add(CommitFile(commit_id=c1.id, file_path="configs/settings.yaml", folder="vanilla", change_type="MODIFIED", additions=10, deletions=2))
            db.add(CommitJira(commit_id=c1.id, jira_id=jira))
            
            # Commit 2: MET (Merged after 1-4 days)
            if random.random() < 0.9:
                delay = random.randint(1, 4)
                sha2 = hashlib.sha1(f"{jira}-met".encode()).hexdigest()
                c2 = Commit(
                    sha=sha2,
                    repository_id=repo_id,
                    author_id=auth.id,
                    branch="main",
                    message=f"merge: synced ticket {jira} to MET customer profile",
                    commit_date=base_date + timedelta(days=delay)
                )
                db.add(c2)
                await db.flush()
                
                db.add(CommitFile(commit_id=c2.id, file_path="configs/settings.yaml", folder="MET", change_type="MODIFIED", additions=10, deletions=2))
                db.add(CommitJira(commit_id=c2.id, jira_id=jira))

            # Commit 3: AMO (Merged after 3-10 days, but some tickets won't merge to create violations!)
            should_merge = True
            delay = random.randint(3, 10)
            if idx == 0 or idx == 1:
                should_merge = False  # Missing merges!
            elif idx == 2:
                delay = 18  # High delay violation!

            if should_merge and random.random() < 0.8:
                sha3 = hashlib.sha1(f"{jira}-amo".encode()).hexdigest()
                c3 = Commit(
                    sha=sha3,
                    repository_id=repo_id,
                    author_id=auth.id,
                    branch="main",
                    message=f"merge: deployed {jira} changes to AMO customer folder",
                    commit_date=base_date + timedelta(days=delay)
                )
                db.add(c3)
                await db.flush()
                
                db.add(CommitFile(commit_id=c3.id, file_path="configs/settings.yaml", folder="AMO", change_type="MODIFIED", additions=10, deletions=2))
                db.add(CommitJira(commit_id=c3.id, jira_id=jira))

        await db.commit()

        # 5. Refresh Materialized Views
        print("Refreshing materialized views...")
        await db.execute(text("REFRESH MATERIALIZED VIEW mv_jira_summary"))
        await db.execute(text("REFRESH MATERIALIZED VIEW mv_coverage_matrix"))
        await db.commit()

        # 6. Seed mock file hashes for content verification
        print("Scanning and seeding mock SHA256 hashes...")
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
                total_jiras=20,
                total_commits=50 + i,
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
            
            for folder in ["vanilla", "MET", "AMO"]:
                if folder == "vanilla":
                    base_h = 95.0
                elif folder == "MET":
                    base_h = 75.0 + (progress_ratio * 15.0)
                else:
                    base_h = 60.0 + (progress_ratio * 25.0)
                    
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
        print("✅ Seeding complete! SENTINEL database is now fully populated.")


if __name__ == "__main__":
    asyncio.run(seed_data())
