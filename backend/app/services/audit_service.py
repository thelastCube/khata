"""Read access to the audit log for the UI timeline."""
from ..dao.audit_dao import AuditDao


class AuditService:
    def __init__(self, audit: AuditDao):
        self.audit = audit

    def list(self, entity: str | None = None, month: str | None = None, limit: int = 200) -> list[dict]:
        return self.audit.list(entity=entity, month=month, limit=limit)
