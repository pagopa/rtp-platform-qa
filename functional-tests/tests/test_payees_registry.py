import allure
import pytest

from api.auth import get_access_token
from api.auth import get_valid_access_token
from api.payee_registry import get_payee_registry
from config.configuration import config
from config.configuration import secrets

PAYEES_URL = f"{config.rtp_creation_base_url_path}payees"


@allure.feature('Payees Registry')
@allure.story('pagoPA retrieves payees registry')
class TestPayeesRegistry:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.access_token = get_valid_access_token(
            client_id=secrets.pagopa_integration_payee_registry.client_id,
            client_secret=secrets.pagopa_integration_payee_registry.client_secret,
            access_token_function=get_access_token
        )

    @allure.title('Get paginated list of payees successfully')
    @pytest.mark.happy_path
    def test_get_payees_success(self):
        response = get_payee_registry(self.access_token)

        assert response.status_code == 200
        data = response.json()

        assert 'payees' in data
        assert 'page' in data
        assert isinstance(data['payees'], list)

        assert len(data['payees']) > 0, 'Expected at least one payee in the response'

        page_metadata = data['page']
        assert all(key in page_metadata for key in ['totalElements', 'totalPages', 'page', 'size'])

        assert page_metadata['totalElements'] >= len(data['payees']), 'Total elements should be at least the number of payees returned'
        assert page_metadata['totalPages'] > 0, 'Should have at least one page'
        assert page_metadata['page'] >= 0, 'Page number should be non-negative'
        assert page_metadata['size'] > 0, 'Page size should be positive'

        assert page_metadata['totalElements'] <= page_metadata['totalPages'] * page_metadata['size'], 'Total elements should not exceed the capacity of all pages'

        for payee in data['payees']:
            assert 'payeeId' in payee
            assert 'name' in payee
            assert isinstance(payee['payeeId'], str)
            assert isinstance(payee['name'], str)
            assert 1 <= len(payee['payeeId']) <= 30
            assert len(payee['name']) > 0, 'Payee name should not be empty'

    @allure.title('Get payees with invalid authorization')
    @pytest.mark.unhappy_path
    def test_get_payees_invalid_auth(self):
        response = get_payee_registry('invalid_token')

        assert response.status_code == 401
