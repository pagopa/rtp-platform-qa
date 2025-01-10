from datetime import datetime

import allure
import pytest

from api.activation import activate
from api.activation import get_activation_by_payer_id
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
    access_token = get_valid_access_token(client_id=secrets.debtor_service_provider.client_id,
                                          client_secret=secrets.debtor_service_provider.client_secret)
    debtor_fc = fake_fc()

    res = activate(access_token, debtor_fc, secrets.debtor_service_provider.service_provider_id)
    assert res.status_code == 201, 'Error activating debtor'

    location = res.headers['Location']
    location_split = location.split('/')

    assert '/'.join(location_split[:-1]) == config.activation_base_url_path + config.activation_path
    assert bool(uuidv4_pattern.fullmatch(location_split[-1]))

    res = get_activation_by_payer_id(access_token, debtor_fc)
    assert res.status_code == 200
    assert res.json()['payer']['fiscalCode'] == debtor_fc
    assert res.json()['payer']['rtpSpId'] == secrets.debtor_service_provider.service_provider_id
    assert bool(uuidv4_pattern.fullmatch(res.json()['id']))

    try:
        datetime.strptime(res.json()['effectiveActivationDate'], '%Y-%m-%dT%H:%M:%S.%f')
    except ValueError:
        assert False, 'Invalid date format'


@allure.feature('Activation')
@allure.story('Debtor activation')
@allure.title('The actiavation request bust contain lower case fiscal code')
@pytest.mark.auth
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_activate_debtor():
    access_token = get_valid_access_token(client_id=secrets.debtor_service_provider.client_id,
                                          client_secret=secrets.debtor_service_provider.client_secret)
    debtor_fc = fake_fc().lower()

    res = activate(access_token, debtor_fc, secrets.debtor_service_provider.service_provider_id)
    assert res.status_code == 400
