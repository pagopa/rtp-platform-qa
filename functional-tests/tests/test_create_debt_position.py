import uuid
import random

import allure
import pytest

from api.debt_position import create_debt_position
from api.activation import activate
from api.auth import get_access_token, get_valid_access_token
from config.configuration import secrets
from utils.dataset import fake_fc


@allure.feature('Debt Positions')
@allure.story('Create Debt Position')
@allure.title('Happy path: a debt position is created and published')
@pytest.mark.debt_positions
@pytest.mark.happy_path
def test_create_debt_position_happy_path():

    access_token = get_valid_access_token(
        client_id=secrets.debtor_service_provider.client_id,
        client_secret=secrets.debtor_service_provider.client_secret,
        access_token_function=get_access_token
    )
    debtor_fc = fake_fc()
    activation_response = activate(
        access_token,
        debtor_fc,
        secrets.debtor_service_provider.service_provider_id
    )
    assert activation_response.status_code == 201, 'Error activating debtor before creating debt position'


    subscription_key = secrets.debt_positions.subscription_key
    organization_id = secrets.debt_positions.organization_id

    iupd = uuid.uuid4().hex
    iuv = ''.join(random.choices('0123456789', k=17))

    payload = {
        "iupd": iupd,
        "type": "F",
        "fiscalCode": debtor_fc,
        "fullName": "John Doe",
        "streetName": "streetName",
        "civicNumber": "11",
        "postalCode": "00100",
        "city": "city",
        "province": "RM",
        "region": "RM",
        "country": "IT",
        "email": "lorem@lorem.com",
        "phone": "333-123456789",
        "companyName": "companyName",
        "officeName": "officeName",
        "switchToExpired": False,
        "paymentOption": [
            {
                "iuv": iuv,
                "amount": 10000,
                "description": "Canone Unico Patrimoniale - CORPORATE",
                "isPartialPayment": False,
                "dueDate": "2025-07-21T12:42:40.625Z",
                "retentionDate": "2025-09-24T12:42:40.625Z",
                "fee": 0,
                "transfer": [
                    {
                        "idTransfer": "1",
                        "amount": 8000,
                        "remittanceInformation": "remittanceInformation 1",
                        "category": "9/0201102IM/",
                        "iban": "IT0000000000000000000000000000"
                    },
                    {
                        "idTransfer": "2",
                        "amount": 2000,
                        "remittanceInformation": "remittanceInformation 2",
                        "category": "9/0201102IM/",
                        "iban": "IT0000000000000000000000000000"
                    }
                ]
            }
        ]
    }

    res = create_debt_position(subscription_key, organization_id, payload, to_publish=True)
    assert res.status_code == 201, f'Expected 201 but got {res.status_code}'

    body = res.json()
    print(body)