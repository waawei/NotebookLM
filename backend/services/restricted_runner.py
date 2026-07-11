import os
import queue
import subprocess
import threading
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
        if not network_allowed and any(argument in {"-S", "-I", "-E"} for argument in command[1:]):
            return RunResult(-1, "", "Python startup options bypass network policy", False, "policy_error")
        env = {
            key: value for key, value in os.environ.items()
            if not any(word in key.upper() for word in self.SENSITIVE)
        }
        if not network_allowed:
            runtime = cwd / ".workflow" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "sitecustomize.py").write_text(
                "import os\nif os.getenv('MODELING_NETWORK_DISABLED') == '1':\n"
                "    import socket, _socket\n"
                "    def denied(*args, **kwargs):\n"
                "        raise RuntimeError('Network access is disabled for this experiment')\n"
                "    socket.socket = denied\n    socket.create_connection = denied\n    _socket.socket = denied\n"
                "    import os, subprocess\n"
                "    def deny_process(*args, **kwargs):\n"
                "        raise RuntimeError('Process creation is disabled for this experiment')\n"
                "    os.system = deny_process\n    subprocess.Popen = deny_process\n"
                "    subprocess.run = deny_process\n    subprocess.call = deny_process\n"
                "    subprocess.check_call = deny_process\n    subprocess.check_output = deny_process\n",
                encoding="utf-8",
            )
            env["MODELING_NETWORK_DISABLED"] = "1"
            env["PYTHONPATH"] = str(runtime)
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False)
        if on_started:
            on_started(process.pid)
        try:
            stdout, stderr = self._collect(process, timeout_seconds, max_output_bytes)
            return RunResult(
                process.returncode, stdout, stderr, False,
                None if process.returncode == 0 else "code_error",
            )
        except subprocess.TimeoutExpired:
            self._kill_tree(process.pid)
            stdout, stderr = self._collect(process, 5, max_output_bytes)
            return RunResult(-1, stdout, stderr or "Execution timed out", True, "resource_error")

    def _collect(self, process, timeout_seconds: int, max_output_bytes: int) -> tuple[str, str]:
        events = queue.Queue()
        threads = [
            threading.Thread(target=self._read_stream, args=(stream, name, events), daemon=True)
            for name, stream in (("stdout", process.stdout), ("stderr", process.stderr))
        ]
        for thread in threads:
            thread.start()
        chunks = {"stdout": bytearray(), "stderr": bytearray()}
        total = 0
        deadline = __import__("time").monotonic() + timeout_seconds
        while any(thread.is_alive() for thread in threads):
            remaining = deadline - __import__("time").monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(process.args, timeout_seconds)
            try:
                name, chunk = events.get(timeout=min(0.1, remaining))
            except queue.Empty:
                continue
            allowance = max_output_bytes - total
            if allowance <= 0:
                self._kill_tree(process.pid)
                raise subprocess.TimeoutExpired(process.args, timeout_seconds)
            chunks[name].extend(chunk[:allowance])
            total += len(chunk)
            if len(chunk) > allowance:
                self._kill_tree(process.pid)
                raise subprocess.TimeoutExpired(process.args, timeout_seconds)
        process.wait(timeout=max(0.1, deadline - __import__("time").monotonic()))
        return tuple(value.decode("utf-8", errors="replace") for value in (chunks["stdout"], chunks["stderr"]))

    @staticmethod
    def _read_stream(stream, name: str, events) -> None:
        for chunk in iter(lambda: stream.read(4096), b""):
            events.put((name, chunk))

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
