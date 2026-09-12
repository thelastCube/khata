"""Label + group management, and on-the-fly label resolution."""
from ..dao.audit_dao import AuditDao
from ..dao.labels_dao import LabelsDao
from ..models import Label


class LabelError(ValueError):
    pass


class LabelService:
    def __init__(self, labels: LabelsDao, audit: AuditDao):
        self.labels = labels
        self.audit = audit

    # --- labels ---
    def list(self) -> list[Label]:
        return self.labels.list()

    def create(self, name: str, color: str | None) -> Label:
        if self.labels.get_by_name(name):
            raise LabelError(f"label '{name}' already exists")
        label = self.labels.create(Label(name=name, color=color))
        self.audit.log("label.create", "label", label.id, {"name": name})
        return label

    def update(self, label_id: int, name: str, color: str | None) -> Label:
        label = self.labels.get(label_id)
        if not label:
            raise LabelError(f"label {label_id} not found")
        clash = self.labels.get_by_name(name)
        if clash and clash.id != label_id:
            raise LabelError(f"label '{name}' already exists")
        label.name, label.color = name, color
        self.labels.update(label)
        self.audit.log("label.update", "label", label_id, {"name": name})
        return label

    def delete(self, label_id: int) -> None:
        self.labels.delete(label_id)
        self.audit.log("label.delete", "label", label_id)

    def resolve_names(self, names: list[str]) -> list[int]:
        """Map label names to ids (case-insensitive), creating any that don't
        exist yet. Deduped — 'Food' and 'food' collapse to one id."""
        ids: list[int] = []
        seen: set[int] = set()
        for raw in names:
            name = raw.strip()
            if not name:
                continue
            existing = self.labels.get_by_name(name)
            if existing:
                lid = existing.id
            else:
                created = self.labels.create(Label(name=name))
                self.audit.log("label.create", "label", created.id, {"name": name, "via": "expense"})
                lid = created.id
            if lid not in seen:
                seen.add(lid)
                ids.append(lid)
        return ids

    # --- groups ---
    def list_groups(self) -> list[dict]:
        out = []
        for g in self.labels.list_groups():
            out.append({"id": g["id"], "name": g["name"], "label_ids": self.labels.group_label_ids(g["id"])})
        return out

    def create_group(self, name: str, label_ids: list[int]) -> dict:
        gid = self.labels.create_group(name)
        self.labels.set_group_labels(gid, label_ids)
        self.audit.log("group.create", "group", gid, {"name": name})
        return {"id": gid, "name": name, "label_ids": label_ids}

    def update_group(self, group_id: int, name: str, label_ids: list[int]) -> dict:
        if not self.labels.get_group(group_id):
            raise LabelError(f"group {group_id} not found")
        self.labels.rename_group(group_id, name)
        self.labels.set_group_labels(group_id, label_ids)
        self.audit.log("group.update", "group", group_id, {"name": name})
        return {"id": group_id, "name": name, "label_ids": label_ids}

    def delete_group(self, group_id: int) -> None:
        self.labels.delete_group(group_id)
        self.audit.log("group.delete", "group", group_id)

    def group_label_ids(self, group_id: int) -> list[int]:
        if not self.labels.get_group(group_id):
            raise LabelError(f"group {group_id} not found")
        return self.labels.group_label_ids(group_id)
