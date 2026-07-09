"""Load and validate local, inspectable agent skill manifests."""

import copy
import json
import os
from typing import Iterable, Optional


DEFAULT_REGISTERED_TOOLS = {
    "retrieve_sources",
    "create_note",
    "create_output",
    "create_wiki_page",
}

REQUIRED_FIELDS = {
    "skill_id",
    "name",
    "description",
    "allowed_tools",
    "prompt_template",
    "output_kind",
}


class SkillService:
    """Read only manifests from the local backend skills directory."""

    def __init__(
        self,
        skills_dir: Optional[str] = None,
        known_tools: Optional[Iterable[str]] = None,
    ):
        self.skills_dir = skills_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "skills"
        )
        self.known_tools = set(known_tools or DEFAULT_REGISTERED_TOOLS)

    def list_skills(self) -> list[dict]:
        """Return validated manifests in stable skill-id order."""
        manifests = []
        for manifest_path in sorted(
            self._manifest_paths(),
            key=lambda path: os.path.basename(os.path.dirname(path)),
        ):
            manifests.append(self._load_manifest(manifest_path))

        skill_ids = [manifest["skill_id"] for manifest in manifests]
        if len(skill_ids) != len(set(skill_ids)):
            raise ValueError("Skill manifests must use unique skill_id values")
        return manifests

    def get_skill(self, skill_id: str) -> Optional[dict]:
        """Return one validated manifest, or ``None`` when it is absent."""
        for manifest in self.list_skills():
            if manifest["skill_id"] == skill_id:
                return copy.deepcopy(manifest)
        return None

    def _manifest_paths(self) -> list[str]:
        if not os.path.isdir(self.skills_dir):
            return []
        return [
            os.path.join(entry.path, "skill.json")
            for entry in os.scandir(self.skills_dir)
            if entry.is_dir() and os.path.isfile(os.path.join(entry.path, "skill.json"))
        ]

    def _load_manifest(self, manifest_path: str) -> dict:
        try:
            with open(manifest_path, "r", encoding="utf-8") as handle:
                manifest = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid skill manifest JSON: {manifest_path}") from exc

        self._validate_manifest(manifest, manifest_path)
        return manifest

    def _validate_manifest(self, manifest: object, manifest_path: str) -> None:
        if not isinstance(manifest, dict):
            raise ValueError(f"Skill manifest must be an object: {manifest_path}")

        missing = sorted(REQUIRED_FIELDS - manifest.keys())
        if missing:
            raise ValueError(
                f"Skill manifest {manifest_path} is missing required fields: {', '.join(missing)}"
            )

        for field in REQUIRED_FIELDS - {"allowed_tools"}:
            if not isinstance(manifest[field], str) or not manifest[field].strip():
                raise ValueError(f"Skill manifest field {field} must be a non-empty string")

        allowed_tools = manifest["allowed_tools"]
        if not isinstance(allowed_tools, list) or not all(
            isinstance(tool_name, str) and tool_name for tool_name in allowed_tools
        ):
            raise ValueError("Skill manifest allowed_tools must be a list of tool names")

        unknown_tools = sorted(set(allowed_tools) - self.known_tools)
        if unknown_tools:
            raise ValueError(
                "Skill manifest references unregistered tools: "
                + ", ".join(unknown_tools)
            )
