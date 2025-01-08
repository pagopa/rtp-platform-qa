import allure
import pytest

from api.activation import activate
from api.auth import get_valid_access_token
from config.configuration import config
from config.configuration import secrets
from utils.dataset import fake_fc
from utils.dataset import uuidv4_pattern


@allure.feature('Activation')
@allure.story('Debtor activation')
@allure.title('A debtor is activated by an authenticated service provider')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.happy_path
def test_activate_debtor():
    access_token = get_valid_access_token(client_id=secrets.debtor_service_provider.client_id, client_secret=secrets.debtor_service_provider.client_secret)
    debtor_fc = fake_fc()

    res = activate(access_token, debtor_fc, secrets.debtor_service_provider.service_provider_id)
    assert res.status_code == 201, 'Error activating debtor'

    location = res.headers['Location']
    location_split = location.split('/')

    assert '/'.join(location_split[:-1]) == config.activation_base_url_path + config.activation_path
    assert bool(uuidv4_pattern.fullmatch(location_split[-1]))
