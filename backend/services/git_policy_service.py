import difflib
import hashlib
import re
import subprocess
from pathlib import Path, PurePosixPath


FORBIDDEN_PARTS = {".env", ".venv", "__pycache__", ".pytest_cache", ".workflow/build"}
SECRET_PATTERN = re.compile(r"(?i)(api[_-]?key|access[_-]?token|secret|password|authorization)\s*[:=]\s*[^\s]+")
MAX_GIT_FILE_BYTES = 20 * 1024 * 1024
MAX_REVIEW_BYTES = 2 * 1024 * 1024


class GitPolicyService:
    def status(self, project: dict) -> dict:
        root = self._root(project)
        result = self._git(root, ["status", "--porcelain=v1", "--untracked-files=all"])
        return {"paths": sorted(line[3:] for line in result.stdout.splitlines() if len(line) > 3)}

    def review(self, project: dict, paths: list[str]) -> dict:
        root = self._root(project)
        normalized, issues = self.validate_paths(root, paths)
        if issues:
            return {"ok": False, "paths": normalized, "issues": issues, "diff": ""}
        diff_parts = []
        for relative in normalized:
            path = resolve_git_path(root, relative)
            if self._is_tracked(root, relative):
                diff_parts.append(self._git(root, ["diff", "--no-ext-diff", "--binary", "--", relative]).stdout)
            else:
                diff_parts.append(self._untracked_diff(relative, path))
        diff = "".join(diff_parts)
        if len(diff.encode("utf-8")) > MAX_REVIEW_BYTES:
            diff = diff.encode("utf-8")[:MAX_REVIEW_BYTES].decode("utf-8", errors="ignore") + "\n[diff truncated]\n"
        return {"ok": True, "paths": normalized, "issues": [], "diff": diff}

    def validate_paths(self, root: Path, paths: list[str]) -> tuple[list[str], list[dict]]:
        normalized = sorted({PurePosixPath(path.replace("\\", "/")).as_posix() for path in paths})
        issues = []
        for relative in normalized:
            try:
                candidate = root / relative
                path = resolve_git_path(root, relative)
            except ValueError as error:
                candidate = root / relative
                if candidate.is_symlink():
                    issues.append({"path": relative, "code": "external_symlink", "message": "Symlink resolves outside project workspace"})
                    continue
                issues.append({"path": relative, "code": "invalid_path", "message": str(error)})
                continue
            parts = set(PurePosixPath(relative).parts)
            if relative in FORBIDDEN_PARTS or parts & (FORBIDDEN_PARTS - {".workflow/build"}) or relative.startswith(".workflow/build/"):
                issues.append({"path": relative, "code": "forbidden_path", "message": "Path is excluded from Git delivery"})
            elif not path.exists() or not path.is_file():
                issues.append({"path": relative, "code": "missing_file", "message": "Git path does not name a file"})
            elif path.stat().st_size > MAX_GIT_FILE_BYTES:
                issues.append({"path": relative, "code": "file_too_large", "message": "File exceeds 20 MiB policy limit"})
            elif self._contains_secret(path):
                issues.append({"path": relative, "code": "secret_detected", "message": "File contains a secret-like assignment"})
        return normalized, issues

    def file_hashes(self, project: dict, paths: list[str]) -> dict[str, str]:
        root = self._root(project)
        normalized, issues = self.validate_paths(root, paths)
        if issues:
            raise ValueError("Git policy review failed")
        return {relative: hashlib.sha256(resolve_git_path(root, relative).read_bytes()).hexdigest() for relative in normalized}

    @staticmethod
    def _root(project: dict) -> Path:
        root = Path(project["workspace_path"]).resolve()
        if not (root / ".git").exists():
            raise ValueError("Independent project repository is unavailable")
        return root

    @staticmethod
    def _contains_secret(path: Path) -> bool:
        try:
            return bool(SECRET_PATTERN.search(path.read_text(encoding="utf-8")))
        except UnicodeDecodeError:
            return False

    def _is_tracked(self, root: Path, relative: str) -> bool:
        return self._git(root, ["ls-files", "--error-unmatch", "--", relative], check=False).returncode == 0

    @staticmethod
    def _untracked_diff(relative: str, path: Path) -> str:
        try:
            content = path.read_text(encoding="utf-8").splitlines(keepends=True)
        except UnicodeDecodeError:
            return f"Binary file {relative} sha256 {hashlib.sha256(path.read_bytes()).hexdigest()}\n"
        return "".join(difflib.unified_diff([], content, fromfile="/dev/null", tofile=f"b/{relative}"))

    @staticmethod
    def _git(root: Path, arguments: list[str], check: bool = True):
        return subprocess.run(["git", *arguments], cwd=root, capture_output=True, text=True, check=check)


def resolve_git_path(root: Path, relative: str) -> Path:
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError("Git path must be project-relative")
    target = (root / relative).resolve()
    if target == root or root not in target.parents:
        raise ValueError("Git path escapes project workspace")
    return target
