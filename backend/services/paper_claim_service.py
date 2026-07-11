class PaperClaimService:
    def __init__(self, store):
        self.store = store

    def replace_for_paper(
        self, project_id: str, paper_artifact_id: str, claims: list[dict]
    ) -> list[dict]:
        self.store.replace_paper_claims(project_id, paper_artifact_id, claims)
        return self.store.list_paper_claims(project_id, paper_artifact_id)
