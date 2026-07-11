import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock

from api import modeling


def test_save_markdown_creates_new_artifact_version(monkeypatch, tmp_path):
    project = {"project_id": "p-1", "workspace_path": str(tmp_path)}
    monkeypatch.setattr(modeling, "project_service", Mock(get_project=Mock(return_value=project)))
    artifact_service = Mock()
    artifact_service.register.return_value = {"artifact_id": "paper-2", "version": 2}
    monkeypatch.setattr(modeling, "artifact_service", artifact_service)

    result = asyncio.run(modeling.save_paper_markdown("p-1", modeling.PaperSaveRequest(markdown="# Changed")))

    assert result["version"] == 2
    assert (tmp_path / "paper/draft.md").read_text(encoding="utf-8") == "# Changed"


def test_request_final_approval_rejects_failed_review(monkeypatch):
    monkeypatch.setattr(modeling, "project_service", Mock(get_project=Mock(return_value={"project_id": "p-1"})))
    gate = Mock()
    gate._require_current_review.side_effect = ValueError("Paper has blocking review issues")
    monkeypatch.setattr(modeling, "ModelingGateService", Mock(return_value=gate))

    try:
        asyncio.run(modeling.request_final_paper_approval("p-1"))
    except Exception as error:
        assert error.status_code == 409
        assert "blocking review" in error.detail
    else:
        raise AssertionError("Expected blocked approval")
