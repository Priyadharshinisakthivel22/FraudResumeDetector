from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditEvent


async def log_audit_event(db: AsyncSession, candidate_id: int, event_type: str, metadata: dict) -> None:
    db.add(AuditEvent(candidate_id=candidate_id, event_type=event_type, metadata_json=metadata))
    await db.commit()
