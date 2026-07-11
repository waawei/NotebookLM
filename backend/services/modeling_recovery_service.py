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
    def __init__(self, store):
        self.store = store

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
            for experiment in self.store.active_experiments(project["project_id"]):
                self._stop_owned_process(project, experiment.get("pid"))
            target = RECOVERY_TARGETS[project["state"]]
            recovery = self.store.interrupt_active_runs_and_transition(
                project["project_id"], project["state"], target
            )
            if recovery:
                recovered.append(
                    {
                        "project_id": project["project_id"],
                        "recovered_from": project["state"],
                        "recovered_to": target,
                    }
                )
        return recovered

    @staticmethod
    def _stop_owned_process(project: dict, pid: int | None) -> None:
        if not pid or not psutil.pid_exists(pid):
            return
        process = psutil.Process(pid)
        workspace = Path(project["workspace_path"]).resolve()
        command = " ".join(process.cmdline()).lower()
        try:
            cwd = Path(process.cwd()).resolve()
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
            cwd = None
        if str(workspace).lower() not in command and cwd != workspace:
            raise RuntimeError("Refusing to terminate a process not owned by this project")
        for child in process.children(recursive=True):
            child.kill()
        process.kill()
