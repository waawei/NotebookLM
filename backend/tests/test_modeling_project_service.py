from services.modeling_project_service import ModelingProjectService
from services.modeling_store import ModelingStore
from services.modeling_workspace import ModelingWorkspaceService


def test_project_service_creates_repo_and_advances(tmp_path):
    store = ModelingStore(str(tmp_path / "modeling.db"))
    workspace = ModelingWorkspaceService(str(tmp_path / "projects"), str(tmp_path / "app"))
    service = ModelingProjectService(store, workspace)

    project = service.create_project("Sales Forecast")
    advanced = service.advance(project["project_id"])

    assert advanced["state"] == "problem_parsing"
    assert (tmp_path / "projects" / project["slug"] / ".git").is_dir()


def test_project_service_rolls_back_and_lists_projects(tmp_path):
    store = ModelingStore(str(tmp_path / "modeling.db"))
    workspace = ModelingWorkspaceService(str(tmp_path / "projects"), str(tmp_path / "app"))
    service = ModelingProjectService(store, workspace)

    project = service.create_project("Sales Forecast")
    service.advance(project["project_id"])
    rolled_back = service.rollback(project["project_id"], "edit prompt")

    assert rolled_back["state"] == "project_initialized"
    assert service.get_project(project["project_id"])["name"] == "Sales Forecast"
    assert [item["project_id"] for item in service.list_projects()] == [project["project_id"]]
    assert service.list_tasks(project["project_id"]) == []
    assert service.list_runs(project["project_id"]) == []


def test_project_service_cleans_workspace_when_store_create_fails(tmp_path):
    class FailingStore:
        def create_project(self, *_args, **_kwargs):
            raise RuntimeError("database locked")

    workspace = ModelingWorkspaceService(str(tmp_path / "projects"), str(tmp_path / "app"))
    service = ModelingProjectService(FailingStore(), workspace)

    try:
        service.create_project("Sales Forecast")
    except RuntimeError:
        pass
    else:
        raise AssertionError("store failure should propagate")

    assert not (tmp_path / "projects" / "sales-forecast").exists()


def test_project_service_accepts_empty_rollback_reason(tmp_path):
    store = ModelingStore(str(tmp_path / "modeling.db"))
    workspace = ModelingWorkspaceService(str(tmp_path / "projects"), str(tmp_path / "app"))
    service = ModelingProjectService(store, workspace)
    project = service.create_project("Sales Forecast")
    service.advance(project["project_id"])

    rolled_back = service.rollback(project["project_id"], None)

    assert rolled_back["state"] == "project_initialized"
    [transition] = store.list_transitions(project["project_id"])[1:]
    assert transition["reason"] == "rollback"
