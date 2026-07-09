"""
Run local answer-quality evaluation cases.

Initial cases may use empty doc_ids for schema validation. Replace doc_ids with
real uploaded document IDs before using this for answer-quality scoring.
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.chat_service import ChatService  # noqa: E402


def load_cases(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


async def evaluate_case(service: ChatService | None, case: dict) -> dict:
    if not case["doc_ids"]:
        return {
            "case_id": case["case_id"],
            "ok": False,
            "skipped": True,
            "missing_terms": case["expected_terms"],
            "citation_count": 0,
        }

    response = await service.ask(
        question=case["question"],
        doc_ids=case["doc_ids"],
        mode=case["mode"],
    )
    answer = response.answer.lower()
    missing_terms = [
        term
        for term in case["expected_terms"]
        if term.lower() not in answer
    ]
    citation_count = len(response.citations)

    return {
        "case_id": case["case_id"],
        "ok": not missing_terms and (not case["must_cite"] or citation_count > 0),
        "skipped": False,
        "missing_terms": missing_terms,
        "citation_count": citation_count,
    }


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", required=True)
    args = parser.parse_args()

    cases = load_cases(args.cases)
    service = ChatService() if any(case["doc_ids"] for case in cases) else None
    for case in cases:
        result = await evaluate_case(service, case)
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
