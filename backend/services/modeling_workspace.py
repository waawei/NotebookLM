import re
import shutil
import subprocess
from pathlib import Path


class ModelingWorkspaceService:
    def __init__(self, workspace_root: str, source_root: str):
        self.workspace_root = Path(workspace_root).resolve()
        self.source_root = Path(source_root).resolve()

    def create(self, slug: str) -> Path:
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ValueError("Invalid project slug")
        target = (self.workspace_root / slug).resolve()
        if target == self.source_root or self.source_root in target.parents:
            raise ValueError("Modeling workspaces must be outside the application source tree")
        if target != self.workspace_root / slug or target.exists():
            raise ValueError("Project workspace already exists or escapes its root")

        try:
            target.mkdir(parents=True)
            for relative in (
                "problem/original",
                "data/raw",
                "analysis",
                "src",
                "tests",
                "experiments",
                "figures",
                "tables",
                "paper/sections",
                "deliverables",
                ".workflow/runs",
            ):
                (target / relative).mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init"], cwd=target, check=True, capture_output=True, text=True)
        except Exception:
            self.remove_created(target)
            raise
        return target

    def remove_created(self, path: Path) -> None:
        target = Path(path).resolve()
        if target == self.workspace_root or self.workspace_root not in target.parents:
            raise ValueError("Refusing to remove a path outside the modeling workspace root")
        if target.exists():
            shutil.rmtree(target)
