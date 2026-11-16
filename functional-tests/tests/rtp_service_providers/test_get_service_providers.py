import allure
import pytest

from api.rtp_service_providers_api import get_rtp_service_providers
from utils.response_assertions_utils import assert_response_code


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
