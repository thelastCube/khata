"""Label and group CRUD routes."""
from fastapi import APIRouter, Depends

from ..auth import require_auth
from ..deps import label_service
from ..schemas import GroupIn, GroupOut, LabelIn, LabelOut, MessageResponse
from ..services.label_service import LabelService

router = APIRouter(prefix="/labels", tags=["labels"], dependencies=[Depends(require_auth)])


@router.get("", response_model=list[LabelOut])
def list_labels(svc: LabelService = Depends(label_service)):
    return [LabelOut(**label.__dict__) for label in svc.list()]


@router.post("", response_model=LabelOut)
def create_label(body: LabelIn, svc: LabelService = Depends(label_service)):
    return LabelOut(**svc.create(body.name, body.color).__dict__)


@router.put("/{label_id}", response_model=LabelOut)
def update_label(label_id: int, body: LabelIn, svc: LabelService = Depends(label_service)):
    return LabelOut(**svc.update(label_id, body.name, body.color).__dict__)


@router.delete("/{label_id}", response_model=MessageResponse)
def delete_label(label_id: int, svc: LabelService = Depends(label_service)):
    svc.delete(label_id)
    return MessageResponse(message="deleted")


groups_router = APIRouter(prefix="/groups", tags=["groups"], dependencies=[Depends(require_auth)])


@groups_router.get("", response_model=list[GroupOut])
def list_groups(svc: LabelService = Depends(label_service)):
    return [GroupOut(**g) for g in svc.list_groups()]


@groups_router.post("", response_model=GroupOut)
def create_group(body: GroupIn, svc: LabelService = Depends(label_service)):
    return GroupOut(**svc.create_group(body.name, body.label_ids))


@groups_router.put("/{group_id}", response_model=GroupOut)
def update_group(group_id: int, body: GroupIn, svc: LabelService = Depends(label_service)):
    return GroupOut(**svc.update_group(group_id, body.name, body.label_ids))


@groups_router.delete("/{group_id}", response_model=MessageResponse)
def delete_group(group_id: int, svc: LabelService = Depends(label_service)):
    svc.delete_group(group_id)
    return MessageResponse(message="deleted")
