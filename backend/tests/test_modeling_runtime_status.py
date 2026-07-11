import asyncio
import json

from api import modeling
from services.modeling_runtime_status import ModelingRuntimeStatus
from services import modeling_runtime_status


def test_status_reports_tools_without_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "never-return-this")

    result = ModelingRuntimeStatus(str(tmp_path)).status()

    assert set(result) == {"workspace", "python", "git", "xelatex"}
    assert "never-return-this" not in json.dumps(result)
    assert result["workspace"] == {"configured": True, "writable": True}
    assert isinstance(result["git"]["available"], bool)
    assert set(result["xelatex"]) == {"available", "version"}


def test_runtime_endpoint_returns_capability_status(monkeypatch):
    expected = {
        "workspace": {"configured": True, "writable": False},
        "python": {"available": True, "version": "3.11.0"},
        "git": {"available": True, "version": "git version test"},
        "xelatex": {"available": False, "version": None},
    }

    class Status:
        def status(self):
            return expected

    monkeypatch.setattr(modeling, "runtime_status_service", Status())

    assert asyncio.run(modeling.runtime_status()) == expected


def test_probe_never_returns_untrusted_tool_output(monkeypatch):
    class Result:
        returncode = 1
        stdout = ""
        stderr = "LLM_API_KEY=never-return-this C:/private/tool.conf"

    monkeypatch.setattr(modeling_runtime_status.shutil, "which", lambda _: "tool")
    monkeypatch.setattr(modeling_runtime_status.subprocess, "run", lambda *args, **kwargs: Result())

    assert modeling_runtime_status.probe(["tool", "--version"]) == {
        "available": False,
        "version": None,
    }
