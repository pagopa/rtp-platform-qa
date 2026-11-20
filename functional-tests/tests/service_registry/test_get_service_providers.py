import allure
import pytest

from api.rtp_service_providers_api import get_rtp_service_providers
from utils.response_assertions_utils import assert_response_code

# JWT with alg=none and exp=0.
EXPIRED_UNSIGNED_TOKEN = "Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJleHAiOjB9."


@allure.epic("RTP Service Providers API")
@allure.feature("Versioned Service Providers")
@allure.story("Retrieve the v1 service providers collection")
@allure.title("GET v1 service providers omits qsealc_enabled")
@allure.tag("functional", "happy_path", "get", "rtp_service_providers")
@pytest.mark.happy_path
@pytest.mark.get
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
    assert data["tsps"], "Expected at least one technical service provider"

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
    assert data["tsps"], "Expected at least one technical service provider"

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
    assert tsps, "Expected at least one technical service provider"
    assert sps, "Expected at least one service provider"

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
def test_get_service_providers_rejects_missing_or_invalid_auth(
    access_token: str | None,
    auth_case: str,
    version: str,
) -> None:
    response = get_rtp_service_providers(access_token=access_token, version=version)

    assert_response_code(
        response=response,
        expected_code=401,
        operation="GET RTP service providers",
        status=f"{auth_case} authorization with {version}",
    )


@allure.epic("RTP Service Providers API")
@allure.feature("Versioned Service Providers")
@allure.story("Reject credentials without a service providers registry read role")
@allure.title("GET {version} service providers rejects valid token without registry role")
@allure.tag("functional", "unhappy_path", "get", "rtp_service_providers")
@pytest.mark.parametrize("version", ["v1", "v2"], ids=["v1", "v2"])
@pytest.mark.unhappy_path
@pytest.mark.get
def test_get_service_providers_rejects_token_without_registry_role(
    rtp_reader_access_token: str,
    version: str,
) -> None:
    response = get_rtp_service_providers(access_token=rtp_reader_access_token, version=version)

    assert_response_code(
        response=response,
        expected_code=403,
        operation="GET RTP service providers",
        status=f"valid token without registry role with {version}",
    )


@allure.epic("RTP Service Providers API")
@allure.feature("Versioned Service Providers")
@allure.story("Reject requests without a RequestId header")
@allure.title("GET {version} service providers rejects requests missing RequestId")
@allure.tag("functional", "unhappy_path", "get", "rtp_service_providers")
@pytest.mark.parametrize("version", ["v1", "v2"], ids=["v1", "v2"])
@pytest.mark.unhappy_path
@pytest.mark.get
def test_get_service_providers_rejects_missing_request_id(
    pagopa_service_providers_registry_token: str,
    version: str,
) -> None:
    response = get_rtp_service_providers(
        access_token=pagopa_service_providers_registry_token,
        version=version,
        include_request_id=False,
    )

    assert_response_code(
        response=response,
        expected_code=400,
        operation="GET RTP service providers",
        status=f"missing RequestId with {version}",
    )


@allure.epic("RTP Service Providers API")
@allure.feature("Versioned Service Providers")
@allure.story("Reject requests without a Version header")
@allure.title("GET service providers rejects requests missing Version")
@allure.tag("functional", "unhappy_path", "get", "rtp_service_providers")
@pytest.mark.unhappy_path
@pytest.mark.get
def test_get_service_providers_rejects_missing_version(
    pagopa_service_providers_registry_token: str,
) -> None:
    response = get_rtp_service_providers(
        access_token=pagopa_service_providers_registry_token,
        version=None,
    )

    assert_response_code(
        response=response,
        expected_code=404,
        operation="GET RTP service providers",
        status="missing Version",
    )


@allure.epic("RTP Service Providers API")
@allure.feature("Versioned Service Providers")
@allure.story("Reject malformed Version headers")
@allure.title("GET service providers rejects {invalid_case} Version header")
@allure.tag("functional", "unhappy_path", "get", "rtp_service_providers")
@pytest.mark.parametrize(
    ("version", "invalid_case", "expected_code"),
    [
        pytest.param("v1\x01", "non-printable", 400, id="non-printable"),
        pytest.param("v" * 65, "over-64-characters", 404, id="over-64-characters"),
    ],
)
@pytest.mark.unhappy_path
@pytest.mark.get
def test_get_service_providers_rejects_invalid_version_header(
    pagopa_service_providers_registry_token: str,
    version: str,
    invalid_case: str,
    expected_code: int,
) -> None:
    response = get_rtp_service_providers(
        access_token=pagopa_service_providers_registry_token,
        version=version,
    )

    assert_response_code(
        response=response,
        expected_code=expected_code,
        operation="GET RTP service providers",
        status=f"{invalid_case} Version header",
    )
