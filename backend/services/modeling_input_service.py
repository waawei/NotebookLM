import hashlib
import json
import os
import tempfile
from pathlib import Path, PureWindowsPath


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
        if (
            not filename
            or filename in {".", ".."}
            or any(character in filename for character in ("/", "\\", ":", "\0"))
            or PureWindowsPath(filename).drive
        ):
            raise ValueError("Invalid input filename")
        clean = filename
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

        manifest_path = root / (
            "problem/input_manifest.json"
            if kind == "problem"
            else "data/data_manifest.json"
        )
        previous_manifest = manifest_path.read_bytes() if manifest_path.exists() else None
        manifest = (
            json.loads(previous_manifest.decode("utf-8"))
            if previous_manifest is not None
            else {"files": []}
        )
        if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
            raise ValueError("Input manifest is invalid")
        manifest["files"].append(
            {
                "filename": clean,
                "relative_path": relative.as_posix(),
                "sha256": hashlib.sha256(content).hexdigest(),
                "size": len(content),
            }
        )
        manifest_bytes = (
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        ).encode("utf-8")

        created_target = False
        manifest_replaced = False
        try:
            try:
                handle = target.open("xb")
            except FileExistsError as error:
                raise ValueError("Input file already exists") from error
            created_target = True
            with handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            target.chmod(0o444)
            self._atomic_write(manifest_path, manifest_bytes)
            manifest_replaced = True
            return self.artifact_service.register(
                project_id, f"{kind}_input", relative.as_posix()
            )
        except Exception:
            if manifest_replaced:
                if previous_manifest is None:
                    manifest_path.unlink(missing_ok=True)
                else:
                    self._atomic_write(manifest_path, previous_manifest)
            if created_target and target.exists():
                target.chmod(0o666)
                target.unlink()
            raise

    @staticmethod
    def _atomic_write(path: Path, content: bytes) -> None:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
