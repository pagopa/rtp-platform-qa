import allure
import pytest

from api.auth import get_access_token
from api.auth import get_valid_access_token
from api.service_providers_registry import get_service_providers_registry
from config.configuration import secrets


@allure.feature('Service Providers Registry')
@allure.story('pagoPA retrieves service providers registry')
class TestServiceProvidersRegistry:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.access_token = get_valid_access_token(
            client_id=secrets.pagopa_integration.client_id,
            client_secret=secrets.pagopa_integration.client_secret,
            access_token_function=get_access_token
        )

    @allure.title('Get list of service providers successfully')
    @pytest.mark.happy_path
    def test_get_service_providers_success(self):
        response = get_service_providers_registry(self.access_token)
        print('self.access_token', self.access_token)

        assert response.status_code == 200
        data = response.json()

        assert 'tsps' in data, "Response should contain 'tsps' array"
        assert 'sps' in data, "Response should contain 'sps' array"

        assert isinstance(data['tsps'], list), "'tsps' should be a list"
        assert isinstance(data['sps'], list), "'sps' should be a list"

        assert len(data['tsps']) > 0, "Expected at least one technical service provider"
        assert len(data['sps']) > 0, "Expected at least one service provider"

        for tsp in data['tsps']:
            assert 'id' in tsp, "TSP should have an id"
            assert 'name' in tsp, "TSP should have a name"
            assert 'service_endpoint' in tsp, "TSP should have a service_endpoint"
            assert 'certificate_serial_number' in tsp, "TSP should have a certificate_serial_number"
            assert 'mtls_enabled' in tsp, "TSP should have mtls_enabled flag"

            assert isinstance(tsp['id'], str), "TSP id should be a string"
            assert isinstance(tsp['name'], str), "TSP name should be a string"
            assert isinstance(tsp['service_endpoint'], str), "TSP service_endpoint should be a string"
            assert isinstance(tsp['certificate_serial_number'], str), "TSP certificate_serial_number should be a string"
            assert isinstance(tsp['mtls_enabled'], bool), "TSP mtls_enabled should be a boolean"

            if 'oauth2' in tsp:
                oauth2 = tsp['oauth2']
                assert 'token_endpoint' in oauth2, "OAuth2 should have token_endpoint"
                assert 'method' in oauth2, "OAuth2 should have method"
                assert isinstance(oauth2['token_endpoint'], str), "OAuth2 token_endpoint should be a string"
                assert isinstance(oauth2['method'], str), "OAuth2 method should be a string"

                if 'credentials_transport_mode' in oauth2:
                    assert isinstance(oauth2['credentials_transport_mode'], str)
                if 'client_id' in oauth2:
                    assert isinstance(oauth2['client_id'], str)
                if 'scope' in oauth2:
                    assert isinstance(oauth2['scope'], str)
                if 'mtls_enabled' in oauth2:
                    assert isinstance(oauth2['mtls_enabled'], bool)

        for sp in data['sps']:
            assert 'id' in sp, "SP should have an id"
            assert 'name' in sp, "SP should have a name"
            assert 'tsp_id' in sp, "SP should have a tsp_id"

            assert isinstance(sp['id'], str), "SP id should be a string"
            assert isinstance(sp['name'], str), "SP name should be a string"
            assert isinstance(sp['tsp_id'], str), "SP tsp_id should be a string"

            if 'role' in sp:
                assert isinstance(sp['role'], str), "SP role should be a string"

            tsp_ids = [tsp['id'] for tsp in data['tsps']]
            assert sp['tsp_id'] in tsp_ids, f"SP's tsp_id '{sp['tsp_id']}' should reference an existing TSP"

    @allure.title('Get payees with invalid authorization')
    @pytest.mark.unhappy_path
    def test_get_payees_invalid_auth(self):
        response = get_service_providers_registry('invalid_token')

        assert response.status_code == 401