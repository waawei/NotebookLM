class ModelingAgentRunService:
    def __init__(self, modeling_store, agent_store):
        self.modeling_store = modeling_store
        self.agent_store = agent_store

    def start(
        self,
        project_id: str,
        stage: str,
        role: str,
        skill_id: str,
        inputs: dict,
        required_outputs: list[str],
    ) -> tuple[dict, dict]:
        task = self.modeling_store.create_task(
            project_id, stage, role, inputs, required_outputs
        )
        self.modeling_store.update_task(task["task_id"], "running", 0)
        task["status"] = "running"
        run = self.agent_store.create_agent_run(
            skill_id,
            inputs,
            project_id=project_id,
            task_id=task["task_id"],
            stage=stage,
        )
        return task, run

    def complete(self, task_id: str, run_id: str, artifact_ids: list[str]) -> None:
        self.agent_store.append_agent_step(
            run_id,
            {
                "kind": "artifacts",
                "title": "Registered modeling artifacts",
                "payload": {"artifact_ids": artifact_ids},
            },
        )
        self.agent_store.update_agent_run_status(run_id, "completed")
        self.modeling_store.update_task(task_id, "completed", 0)

    def fail(self, task: dict, run_id: str, safe_error: str) -> None:
        retries = task["retry_count"] + 1
        task["retry_count"] = retries
        task["status"] = "blocked" if retries >= 3 else "failed"
        self.agent_store.append_agent_step(
            run_id,
            {
                "kind": "error",
                "title": "Modeling role failed",
                "payload": {"error": safe_error},
            },
        )
        self.agent_store.update_agent_run_status(run_id, "failed", error=safe_error)
        self.modeling_store.update_task(task["task_id"], task["status"], retries)
