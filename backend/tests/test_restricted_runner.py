import sys

from services.restricted_runner import RestrictedRunner


def test_runner_scrubs_secrets_caps_output_and_denies_network(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "do-not-leak")
    result = RestrictedRunner().run(
        [
            sys.executable,
            "-c",
            "import os, socket; print(os.getenv('LLM_API_KEY')); print('x'*5000); socket.create_connection(('example.com', 80))",
        ],
        tmp_path,
        10,
        1024,
        False,
    )

    assert "do-not-leak" not in result.stdout
    assert len(result.stdout.encode("utf-8")) <= 1024
    assert "Network access is disabled" in result.stderr


def test_runner_kills_timed_out_process(tmp_path):
    result = RestrictedRunner().run(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        tmp_path,
        1,
        1024,
        False,
    )

    assert result.error_code == "resource_error"
    assert result.timed_out is True
