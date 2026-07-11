import subprocess
import sys
from pathlib import Path


class ProjectEnvironmentService:
    def ensure_created(self, project: dict) -> Path:
        root = Path(project["workspace_path"]).resolve()
        python_path = root / ".venv" / "Scripts" / "python.exe"
        if not python_path.is_file():
            subprocess.run(
                [sys.executable, "-m", "venv", str(root / ".venv")],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
        return python_path.resolve()

    def dependency_install_command(self, project: dict) -> list[str]:
        return [
            str(self.ensure_created(project)),
            "-m",
            "pip",
            "install",
            "--requirement",
            "requirements.txt",
        ]
