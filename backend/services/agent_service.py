"""Inspectable execution flow for local, manifest-defined agent skills."""

import json
from typing import Callable, Optional

from services.document_metadata_store import DocumentMetadataStore
from services.llm_service import LLMService
from services.local_llm_config import LLMConfigurationService
from services.skill_service import SkillService
from services.tool_registry import ToolRegistry


class AgentService:
    """Execute one declared skill using only its registered backend tools."""

    def __init__(
        self,
        metadata_store: Optional[DocumentMetadataStore] = None,
        skill_service: Optional[SkillService] = None,
        tool_registry: Optional[ToolRegistry] = None,
        llm_service: Optional[LLMService] = None,
        llm_factory: Optional[Callable[[], LLMService]] = None,
        error_sanitizer: Optional[Callable[[str], str]] = None,
    ):
        if llm_service is not None and llm_factory is not None:
            raise ValueError("Provide either llm_service or llm_factory")
        self.metadata_store = metadata_store or DocumentMetadataStore()
        self.skill_service = skill_service or SkillService()
        self.tool_registry = tool_registry or ToolRegistry()
        if llm_factory is not None:
            self.llm_factory = llm_factory
        elif llm_service is not None:
            self.llm_factory = lambda: llm_service
        else:
            self.llm_factory = LLMService
        self.error_sanitizer = error_sanitizer or LLMConfigurationService().sanitize

    def create_run(self, skill_id: str, input_payload: dict) -> dict:
        if not self.skill_service.get_skill(skill_id):
            raise ValueError(f"Unknown skill: {skill_id}")
        if not isinstance(input_payload, dict):
            raise ValueError("Agent input must be an object")
        return self.metadata_store.create_agent_run(skill_id, input_payload)

    async def execute_run(self, run_id: str) -> dict:
        run = self.metadata_store.get_agent_run(run_id)
        if not run:
            raise ValueError(f"Agent run {run_id} does not exist")

        llm_service = None
        try:
            skill = self.skill_service.get_skill(run["skill_id"])
            if not skill:
                raise ValueError(f"Unknown skill: {run['skill_id']}")
            self._require_allowed_tool(skill, "retrieve_sources")
            self._require_allowed_tool(skill, "create_output")

            payload = run["input_payload"]
            doc_ids = payload.get("doc_ids", [])
            if not isinstance(doc_ids, list) or not all(isinstance(doc_id, str) for doc_id in doc_ids):
                raise ValueError("doc_ids must be a list of strings")
            request = payload.get("request") or skill["prompt_template"]
            if not isinstance(request, str) or not request.strip():
                raise ValueError("request must be a non-empty string")

            retrieved = await self.tool_registry.run_tool(
                "retrieve_sources",
                {"question": request, "doc_ids": doc_ids},
            )
            if not retrieved["ok"]:
                raise RuntimeError(retrieved["error"])
            sources = retrieved["result"]["sources"]
            self.metadata_store.append_agent_step(
                run_id,
                {
                    "kind": "tool",
                    "title": "Retrieved selected sources",
                    "payload": {"tool": "retrieve_sources", "source_count": len(sources)},
                },
            )

            prompt = self._build_prompt(skill, request, sources)
            llm_service = self.llm_factory()
            content = (await llm_service.generate(prompt)).strip()
            if not content:
                raise RuntimeError("LLM returned empty content")
            self.metadata_store.append_agent_step(
                run_id,
                {
                    "kind": "generation",
                    "title": "Generated skill output",
                    "payload": {"output_kind": skill["output_kind"], "content_length": len(content)},
                },
            )

            output = await self.tool_registry.run_tool(
                "create_output",
                {
                    "kind": skill["output_kind"],
                    "title": skill["name"],
                    "content": content,
                    "source_doc_ids": doc_ids,
                },
            )
            if not output["ok"]:
                raise RuntimeError(output["error"])
            output_id = output["result"]["output_id"]
            self.metadata_store.append_agent_step(
                run_id,
                {
                    "kind": "tool",
                    "title": "Persisted generated output",
                    "payload": {"tool": "create_output", "output_id": output_id},
                },
            )
            self.metadata_store.update_agent_run_status(
                run_id, "completed", output_id=output_id
            )
        except Exception as exc:
            error = self._safe_error_message(exc, llm_service)
            self.metadata_store.append_agent_step(
                run_id,
                {"kind": "error", "title": "Agent run failed", "payload": {"error": error}},
            )
            self.metadata_store.update_agent_run_status(run_id, "failed", error=error)

        return self.metadata_store.get_agent_run(run_id)

    def get_run(self, run_id: str) -> Optional[dict]:
        return self.metadata_store.get_agent_run(run_id)

    def list_runs(self) -> list[dict]:
        return self.metadata_store.list_agent_runs()

    @staticmethod
    def _require_allowed_tool(skill: dict, tool_name: str) -> None:
        if tool_name not in skill["allowed_tools"]:
            raise ValueError(f"Skill {skill['skill_id']} is not allowed to use {tool_name}")

    @staticmethod
    def _build_prompt(skill: dict, request: str, sources: list[dict]) -> str:
        return "\n\n".join(
            [
                skill["prompt_template"],
                f"User request:\n{request}",
                "Retrieved local sources:",
                json.dumps(sources, ensure_ascii=False),
                "Return markdown only and ground every claim in these sources.",
            ]
        )

    def _safe_error_message(self, exc: Exception, llm_service: Optional[LLMService]) -> str:
        error = self.error_sanitizer(str(exc))
        api_key = getattr(llm_service, "api_key", "")
        return error.replace(api_key, "***") if api_key else error
