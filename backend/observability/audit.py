import json
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from collections import deque

logger = logging.getLogger("chatbot.audit")

class StructuredAuditLogger:
    """
    Thread-safe structured audit logger for security, tenant tracking, and compliance.
    Keeps an in-memory sliding buffer of the most recent 1000 events for administrative inspection.
    """
    def __init__(self, buffer_size: int = 1000):
        self._buffer = deque(maxlen=buffer_size)
        self._lock = threading.Lock()

    def log_event(
        self,
        event_type: str,
        actor_id: str,
        tenant_id: str,
        action: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Emits a structured audit log and records it in the in-memory audit ring-buffer.
        """
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "actor_id": str(actor_id or "anonymous"),
            "tenant_id": str(tenant_id or "default-tenant"),
            "action": action,
            "status": status,
            "details": details or {}
        }

        with self._lock:
            self._buffer.append(record)

        # Emit structured JSON log
        logger.info(
            f"AUDIT {event_type} | {actor_id}@{tenant_id} | {action} → {status}",
            extra=record
        )
        return record

    def get_recent_events(self, tenant_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieves recent audit events, optionally filtered by tenant_id.
        """
        with self._lock:
            events = list(self._buffer)

        if tenant_id and tenant_id != "global":
            events = [e for e in events if e.get("tenant_id") == tenant_id]

        events.reverse()
        return events[:limit]


# Global Singleton
audit_logger = StructuredAuditLogger()

def log_audit_event(
    event_type: str,
    actor_id: str,
    tenant_id: str,
    action: str,
    status: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    return audit_logger.log_event(
        event_type=event_type,
        actor_id=actor_id,
        tenant_id=tenant_id,
        action=action,
        status=status,
        details=details
    )

def get_audit_logs(tenant_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    return audit_logger.get_recent_events(tenant_id=tenant_id, limit=limit)
