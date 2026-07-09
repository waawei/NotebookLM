import unittest

import httpx
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)

from services.llm_diagnostics import build_connection_diagnostic, sanitize_connection_summary


class LLMConnectionDiagnosticTests(unittest.TestCase):
    def test_rate_limit_diagnostic_exposes_status_and_redacts_provider_message(self):
        error = RateLimitError(
            "request failed",
            response=httpx.Response(
                429,
                request=httpx.Request(
                    "POST",
                    "https://gateway.test/v1/chat/completions",
                ),
            ),
            body={
                "error": {
                    "message": (
                        "Bearer saved-secret at "
                        "https://gateway.test/reset?token=sk-abcdefghijk"
                    )
                }
            },
        )

        diagnostic = build_connection_diagnostic(error, "saved-secret")

        self.assertEqual(diagnostic["phase"], "chat_completion")
        self.assertEqual(diagnostic["status_code"], 429)
        self.assertEqual(diagnostic["category"], "rate_limited")
        self.assertNotIn("saved-secret", diagnostic["summary"])
        self.assertNotIn("gateway.test", diagnostic["summary"])
        self.assertNotIn("sk-abcdefghijk", diagnostic["summary"])

    def test_timeout_has_no_status_and_unknown_error_never_exposes_text(self):
        timeout = APITimeoutError(
            request=httpx.Request(
                "POST",
                "https://gateway.test/v1/chat/completions",
            )
        )

        timeout_diagnostic = build_connection_diagnostic(timeout, "")
        unknown_diagnostic = build_connection_diagnostic(
            RuntimeError("private saved-secret details"),
            "saved-secret",
        )

        self.assertEqual(timeout_diagnostic["category"], "timed_out")
        self.assertIsNone(timeout_diagnostic["status_code"])
        self.assertEqual(
            unknown_diagnostic["summary"],
            "No safe upstream summary was available.",
        )

    def test_summary_removes_control_characters_and_truncates_to_280_characters(self):
        summary = sanitize_connection_summary(
            "sk-abcdefghijk\n" + ("x" * 300),
            "",
        )

        self.assertNotIn("sk-abcdefghijk", summary)
        self.assertNotIn("\n", summary)
        self.assertLessEqual(len(summary), 280)

    def test_known_openai_errors_map_to_actionable_categories(self):
        cases = (
            (AuthenticationError, 401, "authentication_failed"),
            (PermissionDeniedError, 403, "permission_denied"),
            (NotFoundError, 404, "model_not_found"),
            (BadRequestError, 400, "invalid_request"),
            (RateLimitError, 429, "rate_limited"),
            (InternalServerError, 503, "upstream_unavailable"),
            (APIStatusError, 502, "upstream_unavailable"),
        )

        for error_type, status_code, expected_category in cases:
            with self.subTest(error_type=error_type.__name__):
                error = error_type(
                    "provider message",
                    response=httpx.Response(
                        status_code,
                        request=httpx.Request("POST", "https://gateway.test/v1/chat/completions"),
                    ),
                    body={"error": {"message": "provider message"}},
                )
                diagnostic = build_connection_diagnostic(error, "")
                self.assertEqual(diagnostic["category"], expected_category)
                self.assertEqual(diagnostic["status_code"], status_code)

        connection_error = APIConnectionError(
            message="connection failed",
            request=httpx.Request("POST", "https://gateway.test/v1/chat/completions"),
        )
        self.assertEqual(
            build_connection_diagnostic(connection_error, "")["category"],
            "connection_failed",
        )


if __name__ == "__main__":
    unittest.main()
