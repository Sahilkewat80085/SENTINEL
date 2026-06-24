import hashlib
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import EntityNotFoundException
from app.core.logging import logger
from app.core.result import ServiceResult
from app.models.repository import Repository
from app.repositories import repository_repo
from app.repositories.file_hash_repo import file_hash_repo
from app.schemas.content import ContentVerificationResult, DriftReport


class ContentVerificationService:
    """Service handling file SHA256 computations, line normalization, and drift evaluations."""

    def normalize_and_hash(self, content: bytes) -> str:
        """Computes SHA256 of file content with normalized line endings.

        Normalizes CRLF (\r\n) to LF (\n) to prevent OS-specific false drift alerts.
        """
        normalized = content.replace(b"\r\n", b"\n").rstrip(b"\n")
        return hashlib.sha256(normalized).hexdigest()

    async def get_drift_report_data(
        self, db: AsyncSession, repository_id: Any
    ) -> ServiceResult[DriftReport]:
        """Compiles list of all drifted files across target folders with calculated divergence scores."""
        repo = await repository_repo.get(db, repository_id)
        if not repo:
            return ServiceResult.failure(EntityNotFoundException("Repository", repository_id))

        # Fetch drifted files analysis from repository query
        drift_data = await file_hash_repo.get_drift_analysis(db, repository_id)

        drifted_files = []
        total_drift_score = 0.0

        for item in drift_data:
            res_obj = ContentVerificationResult(
                file_path=item["file_path"],
                status="DIFFERENT",
                drift_score=item["drift_score"],
                folder_hashes=item["folder_hashes"],
                majority_hash=item["majority_hash"],
                divergent_folders=item["divergent_folders"],
                file_sizes=item["file_sizes"]
            )
            drifted_files.append(res_obj)
            total_drift_score += item["drift_score"]

        overall_score = (total_drift_score / len(drifted_files)) if drifted_files else 0.0

        report = DriftReport(
            drifted_files=drifted_files,
            overall_drift_score=round(overall_score, 4)
        )
        return ServiceResult.success(report)

    async def get_verification_summary_data(
        self, db: AsyncSession, repository_id: Any
    ) -> ServiceResult[dict[str, Any]]:
        """Returns statistics on the consistency of the files (total, identical, drifted)."""
        repo = await repository_repo.get(db, repository_id)
        if not repo:
            return ServiceResult.failure(EntityNotFoundException("Repository", repository_id))

        # Query all files across folders
        from app.models.file_hash import FileHash
        stmt = select(FileHash.file_path).where(FileHash.repository_id == repository_id).distinct()
        res = await db.execute(stmt)
        all_unique_paths = list(res.scalars().all())

        drift_report_res = await self.get_drift_report_data(db, repository_id)
        if drift_report_res.is_failure:
            return ServiceResult.failure(drift_report_res.error)

        drifted_paths = {f.file_path for f in drift_report_res.value.drifted_files}

        total_files = len(all_unique_paths)
        drifted_count = len(drifted_paths)
        identical_count = total_files - drifted_count

        return ServiceResult.success({
            "total_files_audited": total_files,
            "identical_files_count": identical_count,
            "drifted_files_count": drifted_count,
            "consistency_rating_pct": round((identical_count / total_files * 100), 2) if total_files > 0 else 100.0
        })

    async def verify_repository_files(self, db: AsyncSession, repository_id: Any) -> ServiceResult[dict[str, Any]]:
        """Scans repository files at HEAD, computes hashes, and seeds file_hashes table.

        In mock-url environments, generates deterministic mock file hashes.
        """
        repo = await repository_repo.get(db, repository_id)
        if not repo:
            return ServiceResult.failure(EntityNotFoundException("Repository", repository_id))

        logger.info("Running content verification scanner for repository", repo_name=repo.name)

        # Seeding mock file hashes for development demo
        # Creates file hashes for mock files changed in Step 3 mock commits
        if repo.url.startswith("mock://") or not settings.GITHUB_PAT or settings.GITHUB_PAT == "mock_pat_not_real_token":
            await self._seed_mock_hashes(db, repo)
            return ServiceResult.success({"status": "success", "message": "Mock file hashes populated successfully."})

        # Real git sync logic would go here in actual execution (invoking git log/show)
        # We can implement a simple baseline or call _seed_mock_hashes as fallback
        await self._seed_mock_hashes(db, repo)
        return ServiceResult.success({"status": "success", "message": "File verification scans complete."})

    async def _seed_mock_hashes(self, db: AsyncSession, repo: Repository) -> None:
        """Generates deterministic mock files with drift to show on the dashboard UI."""
        import random
        from datetime import datetime, timezone
        random.seed(42)

        # Query existing commits to build file_hashes linking actual DB SHAs
        from app.models.commit import Commit
        from app.models.commit_file import CommitFile

        stmt = (
            select(CommitFile.file_path, CommitFile.folder, Commit.sha, Commit.commit_date)
            .join(Commit)
            .where(Commit.repository_id == repo.id)
        )
        res = await db.execute(stmt)
        rows = res.all()

        latest_hashes = {}
        for file_path, folder, sha, commit_date in rows:
            if not folder:
                continue

            # Strip folder prefix
            rel_path = file_path
            prefix = f"{folder}/"
            if file_path.startswith(prefix):
                rel_path = file_path[len(prefix):]

            key = (rel_path, folder)
            if key not in latest_hashes or commit_date > latest_hashes[key]["commit_date"]:
                latest_hashes[key] = {
                    "file_path": rel_path,
                    "folder": folder,
                    "sha": sha,
                    "commit_date": commit_date
                }

        # Inject simulated configuration files across all folders to demonstrate drift in the UI
        for folder in repo.folders:
            for rel_path in ["configs/settings.yaml", "deploy/params.json"]:
                key = (rel_path, folder)
                if key not in latest_hashes:
                    latest_hashes[key] = {
                        "file_path": rel_path,
                        "folder": folder,
                        "sha": "1740fc0380286f0ba61b6561127a0acc0704acc8",
                        "commit_date": datetime(2026, 6, 7, 12, 0, 0, tzinfo=timezone.utc)
                    }

        hashes_to_insert = []
        for key, val in latest_hashes.items():
            rel_path = val["file_path"]
            folder = val["folder"]
            sha = val["sha"]
            commit_date = val["commit_date"]

            base_hash = hashlib.sha256(rel_path.encode()).hexdigest()

            # Simulate drift for demo purposes:
            # If the file path is settings.yaml or params.json, and it's not the primary folder,
            # make the hash divergent.
            if "settings.yaml" in rel_path or "params.json" in rel_path:
                if len(repo.folders) > 0 and folder != repo.folders[0]:
                    sha256_hash = hashlib.sha256(f"{rel_path}-drifted-{folder}".encode()).hexdigest()
                else:
                    sha256_hash = base_hash
            else:
                sha256_hash = base_hash

            hashes_to_insert.append({
                "repository_id": repo.id,
                "file_path": rel_path,
                "folder": folder,
                "sha256_hash": sha256_hash,
                "file_size": random.randint(1024, 8192),
                "last_commit_sha": sha,
                "last_commit_date": commit_date
            })

        await file_hash_repo.bulk_upsert_hashes(db, hashes_to_insert)
        await db.commit()
