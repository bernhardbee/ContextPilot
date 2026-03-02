"""
Security audit event persistence utilities.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import Request

from database import get_db_session
from logger import logger
from models import SecurityEvent


def _request_metadata(request: Optional[Request]) -> dict:
    if request is None:
        return {
            "request_id": None,
            "method": None,
            "path": None,
            "client_ip": None,
        }

    return {
        "request_id": getattr(request.state, "request_id", None),
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host if request.client else None,
    }


def persist_security_event(
    event: str,
    outcome: str,
    request: Optional[Request] = None,
    actor: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Persist a security event to database without interrupting request flow on failure."""
    try:
        from db_models import SecurityEventDB

        metadata = _request_metadata(request)
        event_details = details or {}

        with get_db_session() as db:
            db.add(SecurityEventDB(
                event=event,
                outcome=outcome,
                request_id=metadata["request_id"],
                method=metadata["method"],
                path=metadata["path"],
                client_ip=metadata["client_ip"],
                actor=actor,
                details=event_details,
                created_at=datetime.utcnow(),
            ))
    except Exception as exc:
        logger.warning(f"Failed to persist security event '{event}:{outcome}': {exc}")


def list_security_events(
    limit: int = 50,
    offset: int = 0,
    event: Optional[str] = None,
    outcome: Optional[str] = None,
    request_id: Optional[str] = None,
) -> List[SecurityEvent]:
    """Fetch persisted security events with optional filters."""
    from db_models import SecurityEventDB

    with get_db_session() as db:
        query = db.query(SecurityEventDB).order_by(SecurityEventDB.created_at.desc())
        if event:
            query = query.filter(SecurityEventDB.event == event)
        if outcome:
            query = query.filter(SecurityEventDB.outcome == outcome)
        if request_id:
            query = query.filter(SecurityEventDB.request_id == request_id)

        rows = query.offset(offset).limit(limit).all()

        return [
            SecurityEvent(
                id=row.id,
                event=row.event,
                outcome=row.outcome,
                request_id=row.request_id,
                method=row.method,
                path=row.path,
                client_ip=row.client_ip,
                actor=row.actor,
                details=row.details or {},
                created_at=row.created_at,
            )
            for row in rows
        ]
