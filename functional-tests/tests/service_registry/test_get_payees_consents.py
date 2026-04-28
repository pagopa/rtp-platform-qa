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
def test_get_payees_consents_returns_200(debtor_service_provider_token_a: str) -> None:
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")

    response = get_payees_consents(
        access_token=debtor_service_provider_token_a,
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
