from typing import Any, Dict, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository class handling logging of administrative or operational actions for security audits."""

    def __init__(self) -> None:
        super().__init__(AuditLog)

    async def log_action(
        self,
        db: AsyncSession,
        *,
        user_id: Optional[uuid.UUID] = None,
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Create and persist a new security/administrative audit log entry."""
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
            ip_address=ip_address
        )
        db.add(audit_entry)
        await db.flush()
        return audit_entry


# Singleton instance
audit_repo = AuditLogRepository()
