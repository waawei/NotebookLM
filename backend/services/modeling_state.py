from typing import Final


class WorkflowTransitionError(ValueError):
    """Raised when a project requests an illegal workflow transition."""


STATES: Final[tuple[str, ...]] = (
    "project_initialized",
    "problem_parsing",
    "data_profiling",
    "model_planning",
    "model_approval_pending",
    "experiment_implementation",
    "execution_approval_pending",
    "experiment_running",
    "result_validation",
    "paper_drafting",
    "consistency_review",
    "final_approval_pending",
    "packaging",
    "commit_approval_pending",
    "committing",
    "completed",
)
INITIAL_STATE: Final[str] = STATES[0]
TERMINAL_STATE: Final[str] = STATES[-1]
_NEXT: Final[dict[str, str]] = dict(zip(STATES, STATES[1:]))
_ROLLBACK: Final[dict[str, str]] = {
    "problem_parsing": "project_initialized",
    "data_profiling": "problem_parsing",
    "model_planning": "data_profiling",
    "model_approval_pending": "model_planning",
    "experiment_implementation": "model_planning",
    "execution_approval_pending": "experiment_implementation",
    "experiment_running": "experiment_implementation",
    "result_validation": "experiment_implementation",
    "paper_drafting": "result_validation",
    "consistency_review": "paper_drafting",
    "final_approval_pending": "paper_drafting",
    "packaging": "paper_drafting",
    "commit_approval_pending": "packaging",
    "committing": "packaging",
}


def next_state(current: str) -> str:
    try:
        return _NEXT[current]
    except KeyError as exc:
        raise WorkflowTransitionError(f"Cannot advance workflow state: {current}") from exc


def previous_state(current: str) -> str:
    try:
        return _ROLLBACK[current]
    except KeyError as exc:
        raise WorkflowTransitionError(f"Cannot roll back workflow state: {current}") from exc
