import hashlib
import json
from pathlib import Path, PurePath


class ModelingInputService:
    PROBLEM_SUFFIXES = {".pdf", ".md", ".txt"}
    DATA_SUFFIXES = {".csv"}

    def __init__(self, store, artifact_service, max_file_size: int):
        self.store = store
        self.artifact_service = artifact_service
        self.max_file_size = max_file_size

    def import_input(
        self,
        project_id: str,
        filename: str,
        content: bytes,
        kind: str,
    ) -> dict:
        project = self.store.get_project(project_id)
        if not project:
            raise ValueError("Modeling project not found")
        clean = PurePath(filename).name
        if clean != filename or not clean or clean in {".", ".."}:
            raise ValueError("Invalid input filename")
        suffixes = (
            self.PROBLEM_SUFFIXES
            if kind == "problem"
            else self.DATA_SUFFIXES
            if kind == "data"
            else set()
        )
        if Path(clean).suffix.lower() not in suffixes:
            raise ValueError(f"Unsupported {kind} file")
        if len(content) > self.max_file_size:
            raise ValueError("Input file exceeds size limit")

        root = Path(project["workspace_path"])
        relative = Path("problem/original" if kind == "problem" else "data/raw") / clean
        target = root / relative
        if target.exists():
            raise ValueError("Input file already exists")
        target.write_bytes(content)

        manifest_path = root / (
            "problem/input_manifest.json"
            if kind == "problem"
            else "data/data_manifest.json"
        )
        manifest = (
            json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest_path.exists()
            else {"files": []}
        )
        manifest["files"].append(
            {
                "filename": clean,
                "relative_path": relative.as_posix(),
                "sha256": hashlib.sha256(content).hexdigest(),
                "size": len(content),
            }
        )
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        target.chmod(0o444)
        return self.artifact_service.register(
            project_id, f"{kind}_input", relative.as_posix()
        )
