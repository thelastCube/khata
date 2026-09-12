"""Cross-cutting label/group analysis + audit log + CSV backup."""
from fastapi import APIRouter, Depends, Query

from ..auth import require_auth
from ..deps import analysis_service, audit_service, backup_service
from ..services.analysis_service import AnalysisService
from ..services.audit_service import AuditService
from ..services.backup_service import BackupService

router = APIRouter(tags=["analysis"], dependencies=[Depends(require_auth)])


@router.get("/analysis")
def analysis(
    months: list[str] | None = Query(default=None),
    fund_id: int | None = None,
    label_ids: list[int] | None = Query(default=None),
    group_id: int | None = None,
    svc: AnalysisService = Depends(analysis_service),
) -> dict:
    return svc.summarize(months=months, fund_id=fund_id, label_ids=label_ids, group_id=group_id)


@router.get("/audit")
def audit(
    entity: str | None = None,
    month: str | None = None,
    limit: int = 200,
    svc: AuditService = Depends(audit_service),
) -> list[dict]:
    return svc.list(entity=entity, month=month, limit=limit)


@router.post("/backup/export")
def backup_export(svc: BackupService = Depends(backup_service)) -> dict:
    return svc.export_csv()
