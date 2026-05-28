"""Shared schemathesis checks for contract tests.

Defines CONTRACT_CHECKS, the set of checks used by all contract test modules to validate
API responses against the OpenAPI specification.

The custom check ``response_schema_when_body_present`` wraps the standard
``response_schema_conformance`` check and skips validation when the response has no
Content-Type header or an empty body. This avoids false positives caused by APIM
intercepting requests (e.g. when schemathesis injects unknown headers) and returning
a bare 403 with no body, which would otherwise fail schema validation despite being
infrastructure behaviour outside the API contract.
"""
import schemathesis
from schemathesis.checks import CHECKS

schemathesis.checks.load_all_checks()
_response_schema_conformance = CHECKS.get_by_names(["response_schema_conformance"])[0]


@schemathesis.check
def response_schema_when_body_present(ctx, response, case):
    """Validates response body schema only when Content-Type and body are present.

    Skips APIM-intercepted responses (e.g. bare 403 with no body returned when
    schemathesis injects unknown headers), avoiding false positives on infrastructure
    behaviour that is outside the API contract.
    """
    if not response.headers.get("Content-Type") or not response.content:
        return
    _response_schema_conformance(ctx, response, case)


# Checks used across all contract tests:
#   not_a_server_error              — no 5xx responses
#   status_code_conformance         — status code must be documented in the spec
#   response_schema_when_body_present — body must match spec schema (skips bodyless APIM errors)
CONTRACT_CHECKS = CHECKS.get_by_names(["not_a_server_error", "status_code_conformance"]) + [
    response_schema_when_body_present
]
