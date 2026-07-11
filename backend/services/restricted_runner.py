import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import psutil


@dataclass(frozen=True)
class RunResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool
    error_code: str | None


class RestrictedRunner:
    SENSITIVE = ("KEY", "TOKEN", "SECRET", "PASSWORD", "AUTHORIZATION")

    def run(
        self, command: list[str], cwd: Path, timeout_seconds: int,
        max_output_bytes: int, network_allowed: bool, on_started=None,
    ) -> RunResult:
        cwd = Path(cwd).resolve()
        env = {
            key: value for key, value in os.environ.items()
            if not any(word in key.upper() for word in self.SENSITIVE)
        }
        if not network_allowed:
            runtime = cwd / ".workflow" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "sitecustomize.py").write_text(
                "import os\nif os.getenv('MODELING_NETWORK_DISABLED') == '1':\n"
                "    import socket\n"
                "    def denied(*args, **kwargs):\n"
                "        raise RuntimeError('Network access is disabled for this experiment')\n"
                "    socket.socket = denied\n    socket.create_connection = denied\n",
                encoding="utf-8",
            )
            env["MODELING_NETWORK_DISABLED"] = "1"
            env["PYTHONPATH"] = str(runtime)
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if on_started:
            on_started(process.pid)
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
            return RunResult(
                process.returncode, self._truncate(stdout, max_output_bytes),
                self._truncate(stderr, max_output_bytes), False,
                None if process.returncode == 0 else "code_error",
            )
        except subprocess.TimeoutExpired:
            self._kill_tree(process.pid)
            stdout, stderr = process.communicate()
            return RunResult(-1, self._truncate(stdout or "", max_output_bytes), self._truncate(stderr or "Execution timed out", max_output_bytes), True, "resource_error")

    @staticmethod
    def _truncate(value: str, max_output_bytes: int) -> str:
        return value.encode("utf-8")[:max_output_bytes].decode("utf-8", errors="replace")

    @staticmethod
    def _kill_tree(pid: int) -> None:
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
        except psutil.Error:
            return
        for child in children:
            try:
                child.kill()
            except psutil.Error:
                pass
        try:
            parent.kill()
        except psutil.Error:
            pass
