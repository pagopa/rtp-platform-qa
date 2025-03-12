import allure
import pytest

from api.send_rtp import send_rtp_to_mock
from utils.dataset import generate_rtp_data


@allure.feature('RTP Service Provider Mock')
@allure.story('Send an RTP to mocked Service Provider')
@allure.title('The service returns the mocked server error')
@pytest.mark.mock
@pytest.mark.happy_path
def test_mock_reachability():
    rtp_data = generate_rtp_data()
    response = send_rtp_to_mock(rtp_payload=rtp_data)
    assert response.status_code == 201


@allure.feature('RTP Service Provider Mock')
@allure.story('Send an RTP to mocked Service Provider')
@allure.title('The service returns the mocked server error')
@pytest.mark.mock
@pytest.mark.unhappy_path
def test_receive_server_error_from_mock():
    mock_fiscal_code = 'RSSMRA85T10X000D'
    expected_mocked_failure_status_code = 502

    rtp_data = generate_rtp_data()

    rtp_data['payer']['payerId'] = mock_fiscal_code

    response = send_rtp_to_mock(rtp_payload=rtp_data)
    assert response.status_code == expected_mocked_failure_status_code
