import hashlib
import json


def canonical_hash(payload: dict) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class ApprovalService:
    def __init__(self, store):
        self.store = store

    def request(self, project_id: str, gate: str, payload: dict) -> dict:
        if not self.store.get_project(project_id):
            raise ValueError("Modeling project not found")
        return self.store.create_approval_request(
            project_id, gate, payload, canonical_hash(payload)
        )

    def decide(
        self,
        approval_id: str,
        decision: str,
        payload_hash: str,
        comment: str = "",
    ) -> dict:
        if decision not in {"approved", "changes_requested", "rejected"}:
            raise ValueError("Invalid approval decision")
        request = self.store.get_approval_request(approval_id)
        if not request or request["payload_hash"] != payload_hash:
            raise ValueError("Approval payload has changed")
        return self.store.create_approval_decision(
            approval_id, decision, payload_hash, comment
        )

    def require_approved(
        self, project_id: str, gate: str, payload_hash: str
    ) -> dict:
        decision = self.store.find_approved_request(project_id, gate, payload_hash)
        if not decision:
            raise ValueError("Required approval does not match current content")
        return decision

    def remove_request(self, project_id: str, approval_id: str) -> None:
        request = self.store.get_approval_request(approval_id)
        if not request or request["project_id"] != project_id:
            raise ValueError("Approval request not found")
        self.store.delete_approval_request(approval_id)

    def list_for_project(self, project_id: str) -> list[dict]:
        if not self.store.get_project(project_id):
            raise ValueError("Modeling project not found")
        return self.store.list_approval_requests(project_id)
