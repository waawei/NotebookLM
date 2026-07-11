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
        matches = [
            item
            for item in self.modeling_store.list_tasks(project_id)
            if item["stage"] == stage and item["role"] == role
        ]
        previous = matches[-1] if matches else None
        if previous and previous["status"] == "blocked":
            raise ValueError("Modeling task is blocked after 3 failed attempts")
        if previous and previous["status"] == "failed":
            task = previous
        else:
            task = self.modeling_store.create_task(
                project_id, stage, role, inputs, required_outputs
            )
        self.modeling_store.update_task(
            task["task_id"], "running", task["retry_count"]
        )
        task["status"] = "running"
        try:
            run = self.agent_store.create_agent_run(
                skill_id,
                inputs,
                project_id=project_id,
                task_id=task["task_id"],
                stage=stage,
            )
        except Exception:
            retries = task["retry_count"] + 1
            task["retry_count"] = retries
            task["status"] = "blocked" if retries >= 3 else "failed"
            self.modeling_store.update_task(task["task_id"], task["status"], retries)
            raise
        return task, run

    def complete(self, task_id: str, run_id: str, artifact_ids: list[str]) -> None:
        try:
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
        except Exception as error:
            task = self.modeling_store.get_task(task_id)
            retries = (task["retry_count"] if task else 0) + 1
            try:
                self.agent_store.update_agent_run_status(
                    run_id, "failed", error="Modeling role completion failed"
                )
            except Exception:
                pass
            if task:
                try:
                    self.modeling_store.update_task(
                        task_id, "blocked" if retries >= 3 else "failed", retries
                    )
                except Exception:
                    pass
            raise error

    def fail(self, task: dict, run_id: str, safe_error: str) -> None:
        current = self.modeling_store.get_task(task["task_id"]) or task
        retries = current["retry_count"] + 1
        task["retry_count"] = retries
        task["status"] = "blocked" if retries >= 3 else "failed"
        try:
            self.agent_store.append_agent_step(
                run_id,
                {
                    "kind": "error",
                    "title": "Modeling role failed",
                    "payload": {"error": safe_error},
                },
            )
        except Exception:
            pass
        try:
            self.agent_store.update_agent_run_status(
                run_id, "failed", error=safe_error
            )
        except Exception:
            try:
                self.agent_store.update_agent_run_status(
                    run_id, "failed", error=safe_error
                )
            except Exception:
                pass
        self.modeling_store.update_task(task["task_id"], task["status"], retries)
