from pathlib import Path

from services.project_environment_service import ProjectEnvironmentService


def test_environment_service_creates_project_virtual_environment(tmp_path):
    project = {"workspace_path": str(tmp_path)}

    python_path = ProjectEnvironmentService().ensure_created(project)

    assert python_path.is_file()
    assert python_path.parent.parent.name == ".venv"
