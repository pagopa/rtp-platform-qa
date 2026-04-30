from datetime import datetime, timedelta

import allure
import pytest

from api.service_registry_payee_registry_api import get_payees_consents


@allure.epic("Service Registry Payees")
@allure.feature("Payees Consents")
@allure.story("DSP retrieves paginated list of payees consents")
@allure.title("Get paginated list of OPT_OUT payees consents successfully")
@allure.tag("functional", "happy_path", "payees_consents")
@pytest.mark.happy_path
@pytest.mark.get
def test_get_payees_consents_returns_200(pagopa_payees_registry_consent_token: str) -> None:
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")

    response = get_payees_consents(
        access_token=pagopa_payees_registry_consent_token,
        page_number=0,
        page_size=20,
        consent="OPT_OUT",
        from_date=yesterday,
        to_date=today,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    allure.attach(
        body=response.text,
        name="Payees Consents Response",
        attachment_type=allure.attachment_type.JSON,
    )


@allure.epic("Service Registry Payees")
@allure.feature("Payees Consents")
@allure.story("DSP retrieves paginated list of payees consents")
@allure.title("Get payees consents with invalid authorization returns 401")
@allure.tag("functional", "unhappy_path", "payees_consents")
@pytest.mark.unhappy_path
@pytest.mark.get
def test_get_payees_consents_invalid_auth() -> None:
    response = get_payees_consents(access_token="invalid_token")

    assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"


@allure.epic("Service Registry Payees")
@allure.feature("Payees Consents")
@allure.story("DSP retrieves paginated list of payees consents")
@allure.title("Get payees consents with negative page number returns 400")
@allure.tag("functional", "unhappy_path", "payees_consents")
@pytest.mark.unhappy_path
@pytest.mark.get
def test_get_payees_consents_negative_page_number(pagopa_payees_registry_consent_token: str) -> None:
    response = get_payees_consents(
        access_token=pagopa_payees_registry_consent_token,
        page_number=-1,
    )

    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"


@allure.epic("Service Registry Payees")
@allure.feature("Payees Consents")
@allure.story("DSP retrieves paginated list of payees consents")
@allure.title("Get payees consents with negative page size returns 400")
@allure.tag("functional", "unhappy_path", "payees_consents")
@pytest.mark.unhappy_path
@pytest.mark.get
def test_get_payees_consents_negative_page_size(pagopa_payees_registry_consent_token: str) -> None:
    response = get_payees_consents(
        access_token=pagopa_payees_registry_consent_token,
        page_size=-1,
    )

    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"


@allure.epic("Service Registry Payees")
@allure.feature("Payees Consents")
@allure.story("DSP retrieves paginated list of payees consents")
@allure.title("Get payees consents with invalid consent value returns 400")
@allure.tag("functional", "unhappy_path", "payees_consents")
@pytest.mark.unhappy_path
@pytest.mark.get
def test_get_payees_consents_invalid_consent(pagopa_payees_registry_consent_token: str) -> None:
    response = get_payees_consents(
        access_token=pagopa_payees_registry_consent_token,
        consent="INVALID_CONSENT",
    )

    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"


@allure.epic("Service Registry Payees")
@allure.feature("Payees Consents")
@allure.story("DSP retrieves paginated list of payees consents")
@allure.title("Get payees consents with invalid date format returns 400")
@allure.tag("functional", "unhappy_path", "payees_consents")
@pytest.mark.unhappy_path
@pytest.mark.get
def test_get_payees_consents_invalid_date_format(pagopa_payees_registry_consent_token: str) -> None:
    response = get_payees_consents(
        access_token=pagopa_payees_registry_consent_token,
        from_date="invalid-date",
    )

    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"


@allure.epic("Service Registry Payees")
@allure.feature("Payees Consents")
@allure.story("DSP retrieves paginated list of payees consents")
@allure.title("Get payees consents with wrong token type returns 403")
@allure.tag("functional", "unhappy_path", "payees_consents")
@pytest.mark.unhappy_path
@pytest.mark.get
def test_get_payees_consents_wrong_token_type(rtp_reader_access_token: str) -> None:
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")

    response = get_payees_consents(
        access_token=rtp_reader_access_token,
        page_number=0,
        page_size=20,
        consent="OPT_OUT",
        from_date=yesterday,
        to_date=today,
    )

    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
