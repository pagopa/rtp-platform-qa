import time

import allure
import pytest

from api.debtor_activation_api import activate
from api.RTP_get_api import get_rtp_delivery_status
from api.RTP_send_api import send_rtp
from config.configuration import secrets
from utils.dataset_RTP_data import generate_rtp_data
from utils.generators_utils import generate_notice_number
from utils.generators_utils import generate_random_organization_id

_SEND_PROCESSING_WAIT_S = 5

@allure.epic('RTP Get')
@allure.feature('RTP Delivery Status')
@allure.story('Payee checks whether an RTP was delivered')
@allure.title('RTP with status SENT → PD_RTP_DELIVERED with processingDate')
@allure.tag('functional', 'happy_path', 'get', 'rtp_get')
@pytest.mark.get
@pytest.mark.happy_path
def test_get_delivery_status_sent_rtp(
    debtor_service_provider_token_a: str,
    creditor_service_provider_token_a: str,
) -> None:
    """
    Given a debtor is activated and an RTP is sent successfully (status SENT),
    when the payee queries the delivery-status endpoint with the correct
    noticeNumber and payeeId,
    then the response body must contain status=PD_RTP_DELIVERED and a non-null
    processingDate.
    """
    rtp_data = generate_rtp_data()
    payer_id: str = rtp_data['payer']['payerId']
    notice_number: str = rtp_data['paymentNotice']['noticeNumber']
    payee_id: str = rtp_data['payee']['payeeId']

    activation_response = activate(
        debtor_service_provider_token_a,
        payer_id,
        secrets.debtor_service_provider.service_provider_id,
    )
    assert activation_response.status_code == 201, (
        f'Debtor activation failed: {activation_response.status_code} {activation_response.text}'
    )

    send_response = send_rtp(
        access_token=creditor_service_provider_token_a,
        rtp_payload=rtp_data,
    )
    assert send_response.status_code == 201, (
        f'RTP send failed: {send_response.status_code} {send_response.text}'
    )

    time.sleep(_SEND_PROCESSING_WAIT_S)

    delivery_response = get_rtp_delivery_status(
        access_token=debtor_service_provider_token_a,
        notice_number=notice_number,
        payee_id=payee_id,
    )

    assert delivery_response.status_code == 200, (
        f'Expected HTTP 200, got {delivery_response.status_code}: {delivery_response.text}'
    )

    body = delivery_response.json()

    assert body.get('status') == 'PD_RTP_DELIVERED', (
        f"Expected status='PD_RTP_DELIVERED', got status='{body.get('status')}'"
    )
    assert body.get('processingDate') is not None, (
        "Expected 'processingDate' to be non-null for a delivered RTP"
    )


# @allure.epic('RTP Get')
# @allure.feature('RTP Delivery Status')
# @allure.story('Payee checks whether an RTP was delivered')
# @allure.title('RTP with status ERROR_SEND → PD_RTP_NOT_DELIVERED')
# @allure.tag('functional', 'unhappy_path', 'get', 'rtp_get')
# @pytest.mark.get
# @pytest.mark.unhappy_path
# def test_get_delivery_status_error_send_rtp(
#     debtor_service_provider_token_a: str,
#     creditor_service_provider_token_a: str,
# ) -> None:
#     """
#     Given a debtor is activated with a fiscal code that the mock PSP rejects (502),
#     when the RTP transitions to ERROR_SEND and the payee queries the delivery-status
#     endpoint,
#     then the response body must contain status=PD_RTP_NOT_DELIVERED and no processingDate.
#     """
#     rtp_data = generate_rtp_data(payer_id=_MOCK_ERROR_FISCAL_CODE)
#     notice_number: str = rtp_data['paymentNotice']['noticeNumber']
#     payee_id: str = rtp_data['payee']['payeeId']

#     activation_response = activate(
#         debtor_service_provider_token_a,
#         _MOCK_ERROR_FISCAL_CODE,
#         secrets.debtor_service_provider.service_provider_id,
#     )
#     assert activation_response.status_code in (201, 409), (
#         f'Debtor activation failed: {activation_response.status_code} {activation_response.text}'
#     )

#     send_response = send_rtp(
#         access_token=creditor_service_provider_token_a,
#         rtp_payload=rtp_data,
#     )
#     assert send_response.status_code == 201, (
#         f'RTP send failed: {send_response.status_code} {send_response.text}'
#     )

#     time.sleep(_SEND_PROCESSING_WAIT_S)

#     delivery_response = get_rtp_delivery_status(
#         access_token=debtor_service_provider_token_a,
#         notice_number=notice_number,
#         payee_id=payee_id,
#     )

#     assert delivery_response.status_code == 200, (
#         f'Expected HTTP 200, got {delivery_response.status_code}: {delivery_response.text}'
#     )

#     body = delivery_response.json()

#     assert body.get('status') == 'PD_RTP_NOT_DELIVERED', (
#         f"Expected status='PD_RTP_NOT_DELIVERED', got status='{body.get('status')}'"
#     )
#     assert body.get('processingDate') is None, (
#         f"Expected 'processingDate' to be null, got '{body.get('processingDate')}'"
#     )

@allure.epic('RTP Get')
@allure.feature('RTP Delivery Status')
@allure.story('Payee checks whether an RTP was delivered')
@allure.title('Non-existent noticeNumber → PD_RTP_NOT_DELIVERED (non processata)')
@allure.tag('functional', 'unhappy_path', 'get', 'rtp_get')
@pytest.mark.get
@pytest.mark.unhappy_path
def test_get_delivery_status_notice_number_not_found(
    debtor_service_provider_token_a: str,
) -> None:
    """
    Given a noticeNumber that does not correspond to any RTP in the database,
    when the payee queries the delivery-status endpoint,
    then the response must be HTTP 200 with status=PD_RTP_NOT_DELIVERED and no
    processingDate (the debt position is considered "non processata").
    """
    unknown_notice_number: str = generate_notice_number()
    any_payee_id: str = generate_random_organization_id()

    delivery_response = get_rtp_delivery_status(
        access_token=debtor_service_provider_token_a,
        notice_number=unknown_notice_number,
        payee_id=any_payee_id,
    )

    assert delivery_response.status_code == 200, (
        f'Expected HTTP 200, got {delivery_response.status_code}: {delivery_response.text}'
    )

    body = delivery_response.json()

    assert body.get('status') == 'PD_RTP_NOT_DELIVERED', (
        f"Expected status='PD_RTP_NOT_DELIVERED', got status='{body.get('status')}'"
    )
    assert body.get('processingDate') is None, (
        f"Expected 'processingDate' to be null or absent, got '{body.get('processingDate')}'"
    )
