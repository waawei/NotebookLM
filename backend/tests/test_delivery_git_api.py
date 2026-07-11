import asyncio
from unittest.mock import Mock

from api import modeling


def test_delivery_check_maps_missing_project_to_404(monkeypatch):
    monkeypatch.setattr(modeling, "project_service", Mock(get_project=Mock(return_value=None)))

    try:
        asyncio.run(modeling.check_deliverables("missing"))
    except Exception as error:
        assert error.status_code == 404
    else:
        raise AssertionError("Expected missing project error")


def test_request_commit_maps_stale_approval_to_409(monkeypatch):
    monkeypatch.setattr(modeling, "project_service", Mock(get_project=Mock(return_value={"project_id": "p-1"})))
    service = Mock()
    service.request_commit.side_effect = ValueError("Required approval does not match current content")
    monkeypatch.setattr(modeling, "git_commit_service", service)

    try:
        asyncio.run(modeling.request_commit("p-1", modeling.GitCommitRequest(paths=["README.md"], commit_message="feat: delivery")))
    except Exception as error:
        assert error.status_code == 409
    else:
        raise AssertionError("Expected stale approval conflict")
