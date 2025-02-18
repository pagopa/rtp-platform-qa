import allure
import pytest

from api.activation import activate
from api.auth import get_valid_access_token
from api.send_rtp import send_rtp
from config.configuration import secrets
from utils.dataset import generate_rtp_data


@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP')
@allure.title('An RTP is sent through API')
@pytest.mark.send
@pytest.mark.happy_path
def test_send_rtp_api():
    rtp_data = generate_rtp_data()

    debtor_service_provider_access_token = get_valid_access_token(client_id=secrets.debtor_service_provider.client_id,
                                                                  client_secret=secrets.debtor_service_provider.client_secret)
    creditor_service_provider_access_token = get_valid_access_token(
        client_id=secrets.creditor_service_provider.client_id,
        client_secret=secrets.creditor_service_provider.client_secret)

    res = activate(debtor_service_provider_access_token, rtp_data['payer']['payerId'],
                   secrets.debtor_service_provider.service_provider_id)
    assert res.status_code == 201, 'Error activating debtor'

    response = send_rtp(access_token=creditor_service_provider_access_token, rtp_payload=rtp_data)
    assert response.status_code == 201


@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP')
@allure.title('Debtor fiscal code must be lower case during RTP send')
@pytest.mark.send
@pytest.mark.unhappy_path
def test_cannot_send_rtp_api_lower_fiscal_code():
    rtp_data = generate_rtp_data()

    debtor_service_provider_access_token = get_valid_access_token(client_id=secrets.debtor_service_provider.client_id,
                                                                  client_secret=secrets.debtor_service_provider.client_secret)
    creditor_service_provider_access_token = get_valid_access_token(
        client_id=secrets.creditor_service_provider.client_id,
        client_secret=secrets.creditor_service_provider.client_secret)

    res = activate(debtor_service_provider_access_token, rtp_data['payer']['payerId'],
                   secrets.debtor_service_provider.service_provider_id)
    assert res.status_code == 201, 'Error activating debtor'

    rtp_data['payer']['payerId'] = rtp_data['payer']['payerId'].lower()
    response = send_rtp(access_token=creditor_service_provider_access_token, rtp_payload=rtp_data)
    assert response.status_code == 400


@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP')
@allure.title('The service returns the mocked server error')
@pytest.mark.send
@pytest.mark.unhappy_path
def test_receive_server_error_from_mock():
    mock_fiscal_code = 'RSSMRA85T10X000D'
    expected_mocked_failure_status_code = 500

    rtp_data = generate_rtp_data()

    rtp_data['payer']['payerId'] = mock_fiscal_code

    debtor_service_provider_access_token = get_valid_access_token(client_id=secrets.debtor_service_provider.client_id,
                                                                  client_secret=secrets.debtor_service_provider.client_secret)
    creditor_service_provider_access_token = get_valid_access_token(
        client_id=secrets.creditor_service_provider.client_id,
        client_secret=secrets.creditor_service_provider.client_secret)

    activate(debtor_service_provider_access_token, rtp_data['payer']['payerId'],
             secrets.debtor_service_provider.service_provider_id)

    response = send_rtp(access_token=creditor_service_provider_access_token, rtp_payload=rtp_data)
    assert response.status_code == expected_mocked_failure_status_code


@allure.feature('RTP Send')
@allure.story('Service provider sends an RTP')
@allure.title('The response body contains a comprehensible error message')
@pytest.mark.send
@pytest.mark.unhappy_path
def test_field_error_in_body():
    rtp_data = generate_rtp_data()

    debtor_service_provider_access_token = get_valid_access_token(client_id=secrets.debtor_service_provider.client_id,
                                                                  client_secret=secrets.debtor_service_provider.client_secret)
    creditor_service_provider_access_token = get_valid_access_token(
        client_id=secrets.creditor_service_provider.client_id,
        client_secret=secrets.creditor_service_provider.client_secret)

    res = activate(debtor_service_provider_access_token, rtp_data['payer']['payerId'],
                   secrets.debtor_service_provider.service_provider_id)
    assert res.status_code == 201, 'Error activating debtor'

    rtp_data['payee']['payeeId'] = None
    response = send_rtp(access_token=creditor_service_provider_access_token, rtp_payload=rtp_data)
    assert response.status_code == 400
    assert response.json()['error'] == 'NotNull.createRtpDtoMono.payee.payeeId'
    assert response.json()['details'] == 'payee.payeeId must not be null'
