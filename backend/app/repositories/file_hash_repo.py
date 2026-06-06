from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.models.file_hash import FileHash
from app.repositories.base import BaseRepository


class FileHashRepository(BaseRepository[FileHash]):
    """Repository class for file hashes with support for bulk upserts and SQL drift analysis."""

    def __init__(self) -> None:
        super().__init__(FileHash)

    async def get_by_path_and_folder(
        self, db: AsyncSession, repository_id: Any, file_path: str, folder: str
    ) -> Optional[FileHash]:
        """Fetch a specific file hash record."""
        query = select(self.model).where(
            and_(
                self.model.repository_id == repository_id,
                self.model.file_path == file_path,
                self.model.folder == folder
            )
        )
        res = await db.execute(query)
        return res.scalar_one_or_none()

    async def bulk_upsert_hashes(self, db: AsyncSession, hashes_data: List[Dict[str, Any]]) -> None:
        """Bulk inserts or updates file hashes in a single transaction."""
        if not hashes_data:
            return

        for chunk in [hashes_data[i : i + 200] for i in range(0, len(hashes_data), 200)]:
            for item in chunk:
                stmt = (
                    insert(FileHash)
                    .values(
                        repository_id=item["repository_id"],
                        file_path=item["file_path"],
                        folder=item["folder"],
                        sha256_hash=item["sha256_hash"],
                        file_size=item["file_size"],
                        last_commit_sha=item["last_commit_sha"],
                        last_commit_date=item["last_commit_date"],
                    )
                    .on_conflict_do_update(
                        index_elements=["repository_id", "file_path", "folder"],
                        set_={
                            "sha256_hash": item["sha256_hash"],
                            "file_size": item["file_size"],
                            "last_commit_sha": item["last_commit_sha"],
                            "last_commit_date": item["last_commit_date"],
                            "verified_at": text("NOW()"),
                        },
                    )
                )
                await db.execute(stmt)

    async def get_drift_analysis(self, db: AsyncSession, repository_id: Any) -> List[Dict[str, Any]]:
        """Queries for files present in multiple folders that have different SHA256 hashes (drifted files)."""
        query = """
            SELECT file_path, COUNT(DISTINCT sha256_hash) AS distinct_hash_count, COUNT(folder) AS folder_count
            FROM file_hashes
            WHERE repository_id = :repository_id
            GROUP BY file_path
            HAVING COUNT(DISTINCT sha256_hash) > 1
        """
        res = await db.execute(text(query), {"repository_id": repository_id})
        rows = res.all()

        results = []
        for r in rows:
            # Let's query detail hashes for this specific file path to see which folders have what hash
            detail_query = """
                SELECT folder, sha256_hash, file_size, last_commit_sha
                FROM file_hashes
                WHERE repository_id = :repository_id AND file_path = :file_path
            """
            d_res = await db.execute(text(detail_query), {"repository_id": repository_id, "file_path": r.file_path})
            d_rows = d_res.all()

            folder_hashes = {dr.folder: dr.sha256_hash for dr in d_rows}
            folder_sizes = {dr.folder: dr.file_size for dr in d_rows}
            
            # Find the majority hash (mode)
            hash_counts = {}
            for h in folder_hashes.values():
                hash_counts[h] = hash_counts.get(h, 0) + 1
            
            majority_hash = max(hash_counts, key=hash_counts.get)
            divergent_folders = [f for f, h in folder_hashes.items() if h != majority_hash]

            # Compute drift score: 1 - (majority_count / total_folders)
            majority_count = hash_counts[majority_hash]
            total_folders = len(folder_hashes)
            drift_score = 1.0 - (majority_count / total_folders) if total_folders > 0 else 0.0

            results.append({
                "file_path": r.file_path,
                "distinct_hash_count": r.distinct_hash_count,
                "folder_count": r.folder_count,
                "folder_hashes": folder_hashes,
                "file_sizes": folder_sizes,
                "majority_hash": majority_hash,
                "divergent_folders": divergent_folders,
                "drift_score": round(drift_score, 4)
            })

        return results


# Singleton instance
file_hash_repo = FileHashRepository()
