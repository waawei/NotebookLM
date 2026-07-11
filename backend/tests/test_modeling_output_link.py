from services.document_metadata_store import DocumentMetadataStore
from services.output_service import OutputService


def test_modeling_delivery_link_retains_project_and_manifest_references(tmp_path):
    service = OutputService(metadata_store=DocumentMetadataStore(str(tmp_path / "outputs.db")), llm_service=object())

    output = service.create_modeling_delivery_link("project-1", "artifact-1")

    assert output["kind"] == "paper_plan"
    assert "modeling-project://project-1" in output["content"]
    assert "modeling-artifact://artifact-1" in output["content"]
