import hashlib
import subprocess

from services.approval_service import canonical_hash


class GitCommitService:
    def __init__(self, store, approval_service, policy, reproducibility=None, git_run=None):
        self.store = store
        self.approval_service = approval_service
        self.policy = policy
        self.reproducibility = reproducibility
        self._uses_default_git = git_run is None
        self.git_run = git_run or self._git_run

    def request_commit(self, project_id: str, paths: list[str], message: str) -> dict:
        self._require_empty_index(self._project(project_id)["workspace_path"])
        payload = self.current_payload(project_id, paths, message)
        return self.approval_service.request(project_id, "commit_approval", payload)

    def commit(self, project_id: str, paths: list[str], message: str) -> dict:
        project = self._project(project_id)
        payload = self.current_payload(project_id, paths, message)
        payload_hash = canonical_hash(payload)
        self.approval_service.require_approved(project_id, "commit_approval", payload_hash)
        self._require_empty_index(project["workspace_path"])
        self.git_run(["git", "add", "--", *payload["paths"]], cwd=project["workspace_path"])
        staged_paths = self._cached_paths(project["workspace_path"])
        if staged_paths != payload["paths"]:
            raise ValueError("Staged paths do not match approved paths")
        if self._cached_file_hashes(project["workspace_path"], payload["paths"]) != payload["file_hashes"]:
            raise ValueError("Staged file hashes do not match approved content")
        cached = self._cached_diff(project["workspace_path"])
        if cached.returncode == 0:
            raise ValueError("No approved changes are staged")
        if cached.returncode != 1:
            raise ValueError("Unable to inspect staged changes")
        self.git_run(["git", "commit", "-m", payload["commit_message"]], cwd=project["workspace_path"])
        commit_hash = self.git_run(["git", "rev-parse", "HEAD"], cwd=project["workspace_path"]).stdout.strip()
        return self.store.create_project_commit(project_id, payload_hash, commit_hash, payload["commit_message"], payload["manifest_hash"])

    def current_payload(self, project_id: str, paths: list[str], message: str) -> dict:
        project = self._project(project_id)
        clean_message = message.strip()
        if not clean_message or "\n" in clean_message or len(clean_message) > 72:
            raise ValueError("Commit message must be a non-empty subject of at most 72 characters")
        if self.reproducibility and not self.reproducibility.check(project_id)["ok"]:
            raise ValueError("Reproducibility check failed")
        review = self.policy.review(project, paths)
        if not review["ok"]:
            raise ValueError("Git policy review failed")
        manifest = self._manifest(project_id)
        self.policy.file_hashes(project, review["paths"])
        return {"paths": review["paths"], "file_hashes": self._future_staged_hashes(project["workspace_path"], review["paths"]), "diff_hash": hashlib.sha256(review["diff"].encode("utf-8")).hexdigest(), "manifest_hash": manifest["sha256"], "commit_message": clean_message}

    def _manifest(self, project_id: str) -> dict:
        manifests = [item for item in self.store.list_artifacts(project_id) if item["artifact_type"] == "delivery_manifest"]
        if not manifests:
            raise ValueError("Delivery manifest is required")
        return max(manifests, key=lambda item: (item["created_at"], item["artifact_id"]))

    def _project(self, project_id: str) -> dict:
        project = self.store.get_project(project_id)
        if not project:
            raise ValueError("Modeling project not found")
        return project

    @staticmethod
    def _git_run(command: list[str], **kwargs):
        return subprocess.run(command, capture_output=True, text=True, check=True, **kwargs)

    def _cached_diff(self, workspace_path: str):
        if self._uses_default_git:
            return subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=workspace_path, capture_output=True, text=True, check=False)
        return self.git_run(["git", "diff", "--cached", "--quiet"], cwd=workspace_path)

    def _require_empty_index(self, workspace_path: str) -> None:
        if self._cached_paths(workspace_path):
            raise ValueError("Repository already has staged changes")

    def _cached_paths(self, workspace_path: str) -> list[str]:
        if self._uses_default_git:
            result = subprocess.run(["git", "diff", "--cached", "--name-only", "--"], cwd=workspace_path, capture_output=True, text=True, check=True)
        else:
            result = self.git_run(["git", "diff", "--cached", "--name-only", "--"], cwd=workspace_path)
        return sorted(path for path in result.stdout.splitlines() if path)

    def _cached_file_hashes(self, workspace_path: str, paths: list[str]) -> dict[str, str]:
        if self._uses_default_git:
            return {
                path: subprocess.run(["git", "rev-parse", f":{path}"], cwd=workspace_path, capture_output=True, text=True, check=True).stdout.strip()
                for path in paths
            }
        hashes = {}
        for path in paths:
            if self._uses_default_git:
                result = subprocess.run(["git", "show", f":{path}"], cwd=workspace_path, capture_output=True, check=True)
                content = result.stdout
            else:
                result = self.git_run(["git", "show", f":{path}"], cwd=workspace_path)
                content = result.stdout.encode("utf-8")
            hashes[path] = hashlib.sha256(content).hexdigest()
        return hashes

    def _future_staged_hashes(self, workspace_path: str, paths: list[str]) -> dict[str, str]:
        if not self._uses_default_git:
            return self.policy.file_hashes({"workspace_path": workspace_path}, paths)
        return {
            path: subprocess.run(["git", "hash-object", "--path", path, path], cwd=workspace_path, capture_output=True, text=True, check=True).stdout.strip()
            for path in paths
        }
