import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from services.delivery_contracts import DeliveryFile, DeliveryManifest
from services.reproducibility_service import ReproducibilityService
from services.git_policy_service import FORBIDDEN_PARTS, SECRET_PATTERN


class DeliveryService:
    ARCHIVE_ROOTS = ("src", "tests", "paper", "analysis")
    ARCHIVE_FILES = ("README.md", "requirements.txt", "reproduce.ps1")

    def __init__(self, store, artifact_service, output_service=None):
        self.store = store
        self.artifact_service = artifact_service
        self.output_service = output_service
        self.reproducibility = ReproducibilityService(store)

    def build(self, project_id: str) -> dict:
        check = self.reproducibility.check(project_id)
        if not check["ok"]:
            raise ValueError("Reproducibility check failed")
        project = self.store.get_project(project_id)
        root = Path(project["workspace_path"]).resolve()
        deliverables = root / "deliverables"
        deliverables.mkdir(exist_ok=True)
        archive = deliverables / "code.zip"
        self._write_archive(root, archive)
        archive_artifact = self.artifact_service.register(project_id, "delivery_code_archive", "deliverables/code.zip")
        manifest = DeliveryManifest(
            project_id=project_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            reproduction_command=["powershell", "-File", "reproduce.ps1"],
            files=self._files(root, archive),
            experiment_ids=[item["experiment_id"] for item in self.store.list_experiments(project_id) if item["status"] == "completed"],
            paper_claim_count=len(self.store.list_paper_claims(project_id)),
        )
        manifest_path = deliverables / "manifest.json"
        manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        manifest_artifact = self.artifact_service.register(project_id, "delivery_manifest", "deliverables/manifest.json")
        output = None
        if self.output_service:
            output = self.output_service.create_modeling_delivery_link(project_id, manifest_artifact["artifact_id"])
        return {"check": check, "archive_artifact": archive_artifact, "manifest_artifact": manifest_artifact, "output": output}

    def _write_archive(self, root: Path, archive_path: Path) -> None:
        candidates = []
        for root_name in self.ARCHIVE_ROOTS:
            directory = root / root_name
            if directory.is_dir():
                candidates.extend(
                    path
                    for path in directory.rglob("*")
                    if path.is_file()
                    and "__pycache__" not in path.relative_to(root).parts
                    and ".pytest_cache" not in path.relative_to(root).parts
                )
        candidates.extend(root / name for name in self.ARCHIVE_FILES if (root / name).is_file())
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(candidates, key=lambda item: item.relative_to(root).as_posix()):
                self._validate_archive_path(root, path)
                archive.write(path, path.relative_to(root).as_posix())

    def _files(self, root: Path, archive: Path) -> list[DeliveryFile]:
        files = [self._delivery_file(root, archive, "code_archive", True)]
        for relative, role in (("deliverables/paper.pdf", "paper_pdf"), ("paper/draft.md", "paper_markdown"), ("paper/main.tex", "paper_latex"), ("requirements.txt", "dependencies"), ("reproduce.ps1", "reproduction_command")):
            files.append(self._delivery_file(root, root / relative, role, True))
        manifest_path = root / "data" / "data_manifest.json"
        if manifest_path.is_file():
            files.append(self._delivery_file(root, manifest_path, "data_manifest", True))
            try:
                raw = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                raw = []
            entries = raw.get("files", []) if isinstance(raw, dict) else raw
            for entry in entries if isinstance(entries, list) else []:
                relative = entry.get("relative_path") if isinstance(entry, dict) else None
                if isinstance(relative, str):
                    path = root / relative
                    files.append(DeliveryFile(relative_path=relative, sha256=entry.get("sha256", ""), size=path.stat().st_size if path.is_file() else 0, role="raw_data", included_in_git=False, exclusion_reason="restricted_raw_data"))
        for experiment in self.store.list_experiments(self._project_id_for_root(root)):
            if experiment["status"] != "completed":
                continue
            for name in ("config.json", "metrics.json", "environment.json", "run.log"):
                path = root / "experiments" / experiment["experiment_id"] / name
                if path.is_file():
                    files.append(self._delivery_file(root, path, "experiment_evidence", True))
        return sorted(files, key=lambda item: item.relative_path)

    def _project_id_for_root(self, root: Path) -> str:
        for project in self.store.list_projects():
            if Path(project["workspace_path"]).resolve() == root:
                return project["project_id"]
        raise ValueError("Modeling project not found")

    @staticmethod
    def _validate_archive_path(root: Path, path: Path) -> None:
        relative = path.relative_to(root).as_posix()
        if path.is_symlink() and root not in path.resolve().parents:
            raise ValueError("Unsafe archive path")
        if any(part in FORBIDDEN_PARTS for part in Path(relative).parts) or Path(relative).name == ".env":
            raise ValueError("Unsafe archive path")
        try:
            if SECRET_PATTERN.search(path.read_text(encoding="utf-8")):
                raise ValueError("Unsafe archive path")
        except UnicodeDecodeError:
            pass

    @staticmethod
    def _delivery_file(root: Path, path: Path, role: str, included: bool) -> DeliveryFile:
        return DeliveryFile(relative_path=path.relative_to(root).as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest(), size=path.stat().st_size, role=role, included_in_git=included)
