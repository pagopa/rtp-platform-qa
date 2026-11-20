"""Tests for the versioned RTP Service Providers API.

Notes on test assumptions and gateway behavior:
- Test data: Assertions expecting non-empty `tsps` and `sps` lists assume that the target
  environment (e.g., UAT/DEV) has already been seeded with active technical service
  providers and service providers.
- Role isolation: `test_get_service_providers_rejects_token_without_registry_role` relies on
  the `rtp_reader_access_token` client (RTP Reader) lacking the service providers registry
  read role in Keycloak/APIM. A role expansion for this client would cause this test to fail.
- Gateway routing: In Azure API Management (APIM), API versioning is header-based via the
  `Version` header. When this header is missing or contains an unmapped/overlong value,
  APIM fails route resolution at gateway level and returns HTTP 404 Not Found ('Resource not found')
  instead of 400 Bad Request.
"""

import allure
import pytest
from requests import Response

from api.rtp_service_providers_api import get_rtp_service_providers
from utils.response_assertions_utils import assert_response_code

# JWT with alg=none and exp=0.
EXPIRED_UNSIGNED_TOKEN = "Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJleHAiOjB9."


def _assert_error_response(
    response: Response,
    expected_code: int,
    operation: str,
    status: str,
    expected_content_type: str | None = "application/json",
    require_body: bool = True,
) -> None:
    """Assert status code, and optionally non-empty body and Content-Type for error responses."""
    assert_response_code(
        response=response,
        expected_code=expected_code,
        operation=operation,
        status=status,
    )
    if expected_content_type is not None:
        content_type = response.headers.get("Content-Type", "")
        assert expected_content_type in content_type, (
            f"Expected Content-Type containing '{expected_content_type}' for {operation} ({status}), "
            f"got '{content_type}'"
        )
        if "application/json" in expected_content_type:
            try:
                body = response.json()
                assert isinstance(body, dict), f"Expected JSON error body to be an object, got {type(body)}"
                if "statusCode" in body:
                    assert body["statusCode"] == expected_code, (
                        f"Expected body.statusCode to be {expected_code}, got {body['statusCode']}"
                    )
            except ValueError:
                pytest.fail(f"Expected valid JSON in error response for {operation} ({status}): {response.text}")

    if require_body:
        assert response.text.strip(), f"Expected non-empty error body for {operation} ({status})"


@allure.epic("RTP Service Providers API")
@allure.feature("Versioned Service Providers")
@allure.story("Retrieve the v1 service providers collection")
@allure.title("GET v1 service providers omits qsealc_enabled")
@allure.tag("functional", "happy_path", "get", "rtp_service_providers")
@pytest.mark.happy_path
@pytest.mark.get
@pytest.mark.service_registry
def test_get_service_providers_v1_omits_qsealc_enabled(pagopa_service_providers_registry_token: str) -> None:
    response = get_rtp_service_providers(
        access_token=pagopa_service_providers_registry_token,
        version="v1",
    )

    assert_response_code(
        response=response,
        expected_code=200,
        operation="GET RTP service providers",
        status="v1",
    )
    data = response.json()
    assert isinstance(data, dict), "Response body should be an object"
    assert "tsps" in data, "Response should contain 'tsps'"
    assert "sps" in data, "Response should contain 'sps'"
    assert isinstance(data["tsps"], list), "'tsps' should be a list"
    assert isinstance(data["sps"], list), "'sps' should be a list"
    # Note: Assumes the target environment has at least one pre-seeded TSP and SP.
    assert data["tsps"], "Expected at least one technical service provider (assumes pre-seeded environment)"
    assert data["sps"], "Expected at least one service provider (assumes pre-seeded environment)"

    assert all(isinstance(tsp, dict) and "qsealc_enabled" not in tsp for tsp in data["tsps"]), (
        "Every v1 TSP should be an object without 'qsealc_enabled'"
    )


@allure.epic("RTP Service Providers API")
@allure.feature("Versioned Service Providers")
@allure.story("Retrieve the v2 service providers collection")
@allure.title("GET v2 service providers includes qsealc_enabled")
@allure.tag("functional", "happy_path", "get", "rtp_service_providers")
@pytest.mark.happy_path
@pytest.mark.get
@pytest.mark.service_registry
def test_get_service_providers_v2_includes_qsealc_enabled(pagopa_service_providers_registry_token: str) -> None:
    response = get_rtp_service_providers(
        access_token=pagopa_service_providers_registry_token,
        version="v2",
    )

    assert_response_code(
        response=response,
        expected_code=200,
        operation="GET RTP service providers",
        status="v2",
    )
    data = response.json()
    assert isinstance(data, dict), "Response body should be an object"
    assert "tsps" in data, "Response should contain 'tsps'"
    assert "sps" in data, "Response should contain 'sps'"
    assert isinstance(data["tsps"], list), "'tsps' should be a list"
    assert isinstance(data["sps"], list), "'sps' should be a list"
    # Note: Assumes the target environment has at least one pre-seeded TSP and SP.
    assert data["tsps"], "Expected at least one technical service provider (assumes pre-seeded environment)"
    assert data["sps"], "Expected at least one service provider (assumes pre-seeded environment)"

    assert all(isinstance(tsp, dict) and isinstance(tsp.get("qsealc_enabled"), bool) for tsp in data["tsps"]), (
        "Every v2 TSP should include a boolean 'qsealc_enabled'"
    )


@allure.epic("RTP Service Providers API")
@allure.feature("Versioned Service Providers")
@allure.story("Retrieve valid TSP and SP details")
@allure.title("GET {version} service providers returns valid provider details")
@allure.tag("functional", "happy_path", "get", "rtp_service_providers")
@pytest.mark.parametrize("version", ["v1", "v2"], ids=["v1", "v2"])
@pytest.mark.happy_path
@pytest.mark.get
@pytest.mark.service_registry
def test_get_service_providers_returns_valid_provider_details(
    pagopa_service_providers_registry_token: str,
    version: str,
) -> None:
    response = get_rtp_service_providers(
        access_token=pagopa_service_providers_registry_token,
        version=version,
    )

    assert_response_code(
        response=response,
        expected_code=200,
        operation="GET RTP service providers",
        status=version,
    )
    data = response.json()
    assert isinstance(data, dict), "Response body should be an object"
    assert isinstance(data.get("tsps"), list), "'tsps' should be a list"
    assert isinstance(data.get("sps"), list), "'sps' should be a list"
    tsps = data["tsps"]
    sps = data["sps"]
    # Note: Assumes the target environment has at least one pre-seeded TSP and SP.
    assert tsps, "Expected at least one technical service provider (assumes pre-seeded environment)"
    assert sps, "Expected at least one service provider (assumes pre-seeded environment)"

    tsp_string_fields = ("id", "name", "service_endpoint", "certificate_serial_number")
    oauth2_string_fields = (
        "credentials_transport_mode",
        "client_id",
        "client_secret_kv_url",
        "client_secret_env_var",
        "scope",
    )
    assert all(
        isinstance(tsp, dict)
        and all(isinstance(tsp.get(field), str) for field in tsp_string_fields)
        and isinstance(tsp.get("mtls_enabled"), bool)
        and ("takeover_endpoint" not in tsp or isinstance(tsp["takeover_endpoint"], str))
        and (
            "oauth2" not in tsp
            or (
                isinstance(tsp["oauth2"], dict)
                and isinstance(tsp["oauth2"].get("token_endpoint"), str)
                and tsp["oauth2"].get("method") in {"GET", "POST"}
                and all(
                    field not in tsp["oauth2"] or isinstance(tsp["oauth2"][field], str)
                    for field in oauth2_string_fields
                )
                and ("mtls_enabled" not in tsp["oauth2"] or isinstance(tsp["oauth2"]["mtls_enabled"], bool))
            )
        )
        for tsp in tsps
    ), "Every TSP should match the documented response schema"

    sp_string_fields = ("id", "name", "tsp_id")
    assert all(
        isinstance(sp, dict)
        and all(isinstance(sp.get(field), str) for field in sp_string_fields)
        and ("psp_tax_code" not in sp or isinstance(sp["psp_tax_code"], str))
        for sp in sps
    ), "Every SP should match the documented response schema"

    tsp_ids = {tsp["id"] for tsp in tsps}
    assert all(sp["tsp_id"] in tsp_ids for sp in sps), "Every SP should reference an existing TSP"


@allure.epic("RTP Service Providers API")
@allure.feature("Versioned Service Providers")
@allure.story("Reject missing or invalid credentials")
@allure.title("GET {version} service providers rejects {auth_case} authorization")
@allure.tag("functional", "unhappy_path", "get", "rtp_service_providers")
@pytest.mark.parametrize(
    ("access_token", "auth_case"),
    [
        pytest.param(None, "missing", id="missing"),
        pytest.param("invalid_token", "invalid", id="invalid"),
        pytest.param(EXPIRED_UNSIGNED_TOKEN, "expired-and-unsigned", id="expired-unsigned"),
    ],
)
@pytest.mark.parametrize("version", ["v1", "v2"], ids=["v1", "v2"])
@pytest.mark.unhappy_path
@pytest.mark.get
@pytest.mark.service_registry
def test_get_service_providers_rejects_missing_or_invalid_auth(
    access_token: str | None,
    auth_case: str,
    version: str,
) -> None:
    response = get_rtp_service_providers(access_token=access_token, version=version)

    _assert_error_response(
        response=response,
        expected_code=401,
        operation="GET RTP service providers",
        status=f"{auth_case} authorization with {version}",
        expected_content_type="application/json",
    )


@allure.epic("RTP Service Providers API")
@allure.feature("Versioned Service Providers")
@allure.story("Reject credentials without a service providers registry read role")
@allure.title("GET {version} service providers rejects valid token without registry role")
@allure.tag("functional", "unhappy_path", "get", "rtp_service_providers")
@pytest.mark.parametrize("version", ["v1", "v2"], ids=["v1", "v2"])
@pytest.mark.unhappy_path
@pytest.mark.get
@pytest.mark.service_registry
def test_get_service_providers_rejects_token_without_registry_role(
    rtp_reader_access_token: str,
    version: str,
) -> None:
    """Verify that a valid token without the service providers registry read role is rejected with 403.

    Assumption:
        This test relies on `rtp_reader_access_token` (RTP Reader client) lacking the read
        permission for the Service Providers Registry in Keycloak/APIM. A future role change
        granting this client registry access would cause this test to fail.
    """
    response = get_rtp_service_providers(access_token=rtp_reader_access_token, version=version)

    # Note: APIM rejects missing JWT claims/roles at gateway level with an empty 403 Forbidden (no Content-Type).
    _assert_error_response(
        response=response,
        expected_code=403,
        operation="GET RTP service providers",
        status=f"valid token without registry role with {version}",
        expected_content_type=None,
        require_body=False,
    )


@allure.epic("RTP Service Providers API")
@allure.feature("Versioned Service Providers")
@allure.story("Reject requests without a RequestId header")
@allure.title("GET {version} service providers rejects requests missing RequestId")
@allure.tag("functional", "unhappy_path", "get", "rtp_service_providers")
@pytest.mark.parametrize("version", ["v1", "v2"], ids=["v1", "v2"])
@pytest.mark.unhappy_path
@pytest.mark.get
@pytest.mark.service_registry
def test_get_service_providers_rejects_missing_request_id(
    pagopa_service_providers_registry_token: str,
    version: str,
) -> None:
    response = get_rtp_service_providers(
        access_token=pagopa_service_providers_registry_token,
        version=version,
        include_request_id=False,
    )

    _assert_error_response(
        response=response,
        expected_code=400,
        operation="GET RTP service providers",
        status=f"missing RequestId with {version}",
        expected_content_type="application/json",
    )


@allure.epic("RTP Service Providers API")
@allure.feature("Versioned Service Providers")
@allure.story("Reject requests without a Version header")
@allure.title("GET service providers rejects requests missing Version")
@allure.tag("functional", "unhappy_path", "get", "rtp_service_providers")
@pytest.mark.unhappy_path
@pytest.mark.get
@pytest.mark.service_registry
def test_get_service_providers_rejects_missing_version(
    pagopa_service_providers_registry_token: str,
) -> None:
    """Verify that requests missing the Version header are rejected.

    Note on 404 response:
        In Azure API Management (APIM), versioning for this endpoint is configured
        via header routing ('Version' header). When this header is omitted, APIM cannot
        match the request to any registered API version route and responds with
        HTTP 404 Not Found ({"statusCode": 404, "message": "Resource not found"})
        at the gateway routing level, rather than a 400 Bad Request.
    """
    response = get_rtp_service_providers(
        access_token=pagopa_service_providers_registry_token,
        version=None,
    )

    _assert_error_response(
        response=response,
        expected_code=404,
        operation="GET RTP service providers",
        status="missing Version",
        expected_content_type="application/json",
    )


@allure.epic("RTP Service Providers API")
@allure.feature("Versioned Service Providers")
@allure.story("Reject malformed Version headers")
@allure.title("GET service providers rejects {invalid_case} Version header")
@allure.tag("functional", "unhappy_path", "get", "rtp_service_providers")
@pytest.mark.parametrize(
    ("version", "invalid_case", "expected_code", "expected_content_type"),
    [
        # Note: requests does not raise InvalidHeader client-side for \x01 (it only blocks \r and \n).
        # The request reaches the server, where the HTTP layer rejects it with HTTP 400 Bad Request.
        pytest.param("v1\x01", "non-printable", 400, "text/html", id="non-printable"),
        # Note: In APIM, an unmapped/overlong Version header fails gateway version routing,
        # returning HTTP 404 Not Found ("Resource not found") from the gateway.
        pytest.param("v" * 65, "over-64-characters", 404, "application/json", id="over-64-characters"),
    ],
)
@pytest.mark.unhappy_path
@pytest.mark.get
@pytest.mark.service_registry
def test_get_service_providers_rejects_invalid_version_header(
    pagopa_service_providers_registry_token: str,
    version: str,
    invalid_case: str,
    expected_code: int,
    expected_content_type: str,
) -> None:
    response = get_rtp_service_providers(
        access_token=pagopa_service_providers_registry_token,
        version=version,
    )

    _assert_error_response(
        response=response,
        expected_code=expected_code,
        operation="GET RTP service providers",
        status=f"{invalid_case} Version header",
        expected_content_type=expected_content_type,
    )
