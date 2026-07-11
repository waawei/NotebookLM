import subprocess
from pathlib import Path


class EnvironmentCapture:
    def capture(self, python_path: str, cwd: Path) -> dict:
        def run(arguments: list[str]) -> str:
            result = subprocess.run(
                [python_path, *arguments], cwd=cwd, capture_output=True, text=True, check=True
            )
            return result.stdout.strip()

        return {
            "python_version": run(["--version"]),
            "pip_freeze": run(["-m", "pip", "freeze"]).splitlines(),
        }
