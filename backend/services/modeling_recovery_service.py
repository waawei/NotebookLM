from pathlib import Path

import psutil


RECOVERY_TARGETS = {
    "problem_parsing": "project_initialized",
    "data_profiling": "problem_parsing",
    "model_planning": "data_profiling",
    "experiment_implementation": "model_planning",
    "experiment_running": "experiment_implementation",
    "result_validation": "experiment_implementation",
    "paper_drafting": "result_validation",
    "consistency_review": "paper_drafting",
    "packaging": "paper_drafting",
    "committing": "packaging",
}


class ModelingRecoveryService:
    def __init__(self, store, agent_store=None):
        self.store = store
        self.agent_store = agent_store

    def recover_interrupted_projects(self) -> list[dict]:
        recovered = []
        for project in self.store.list_projects_in_states(list(RECOVERY_TARGETS)):
            latest_transition = self.store.latest_transition(project["project_id"])
            if (
                latest_transition
                and latest_transition["reason"] == "interrupted"
                and latest_transition["to_state"] == project["state"]
            ):
                continue
            active_tasks = self.store.active_tasks(project["project_id"])
            interrupted_agent_run_ids = list(
                self._active_agent_run_ids(
                    project["project_id"], {task["task_id"] for task in active_tasks}
                )
            )
            for experiment in self.store.active_experiments(project["project_id"]):
                self._stop_owned_process(project, experiment.get("pid"))
            target = RECOVERY_TARGETS[project["state"]]
            recovery = self.store.interrupt_active_runs_and_transition(
                project["project_id"],
                project["state"],
                target,
                interrupted_agent_run_ids,
            )
            if recovery:
                self._interrupt_agent_runs(interrupted_agent_run_ids)
                recovered.append(
                    {
                        "project_id": project["project_id"],
                        "recovered_from": project["state"],
                        "recovered_to": target,
                    }
                )
        return recovered

    def _active_agent_run_ids(self, project_id: str, task_ids: set[str]) -> list[str]:
        if not self.agent_store or not task_ids:
            return []
        for run in self.agent_store.list_agent_runs(project_id=project_id):
            if run["status"] != "running" or run.get("task_id") not in task_ids:
                continue
            yield run["run_id"]

    def _interrupt_agent_runs(self, run_ids) -> None:
        if not self.agent_store:
            return
        for run_id in run_ids:
            self.agent_store.update_agent_run_status(
                run_id, "failed", error="interrupted"
            )

    @staticmethod
    def _stop_owned_process(project: dict, pid: int | None) -> None:
        if not pid or not psutil.pid_exists(pid):
            return
        try:
            process = psutil.Process(pid)
            workspace = Path(project["workspace_path"]).resolve()
            command = " ".join(process.cmdline()).lower()
            cwd = Path(process.cwd()).resolve()
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
            return
        if str(workspace).lower() not in command and cwd != workspace:
            raise RuntimeError("Refusing to terminate a process not owned by this project")
        try:
            for child in process.children(recursive=True):
                child.kill()
            process.kill()
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            return
