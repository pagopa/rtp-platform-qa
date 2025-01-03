import allure
import pytest

from api.activation import activate
from api.auth import get_valid_access_token
from config.configuration import secrets
from utils.dataset import fake_fc


@allure.feature('Activation')
@allure.story('Debtor activation')
@allure.title('A debtor is activated by an authenticated service provider')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.happy_path
def test_activate_debtor():
    access_token = get_valid_access_token(client_id=secrets.client_id, client_secret=secrets.client_secret)
    debtor_fc = fake_fc()

    res = activate(access_token, debtor_fc, secrets.service_provider_id)
    assert res.status_code == 201, 'Error activating debtor'
