import os
import shutil
import subprocess
import sys
from pathlib import Path


def probe(command: list[str]) -> dict:
    executable = shutil.which(command[0])
    if not executable:
        return {"available": False, "version": None}
    try:
        result = subprocess.run(
            [executable, *command[1:]],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"available": False, "version": None}
    output = result.stdout or result.stderr
    version = output.splitlines()[0][:200] if output else ""
    return {"available": result.returncode == 0, "version": version}


class ModelingRuntimeStatus:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)

    def status(self) -> dict:
        writable = self.workspace_root.exists() and os.access(self.workspace_root, os.W_OK)
        return {
            "workspace": {"configured": True, "writable": writable},
            "python": {"available": True, "version": sys.version.split()[0]},
            "git": probe(["git", "--version"]),
            "xelatex": probe(["xelatex", "--version"]),
        }
