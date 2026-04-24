import uuid

import allure
import pytest

from api.debtor_activation_api import activate
from api.RTP_get_api import get_rtp, get_rtp_optout_payees_list_mock, get_institutions_service_consent_backoffice_optout, get_institutions_service_consent_backoffice_optin, get_payees_consents_optout
from api.RTP_send_api import send_rtp
from config.configuration import secrets
from utils.dataset_RTP_data import generate_rtp_data


@allure.epic("RTP Get")
@allure.feature("RTP Get")
@allure.story("Service provider retrieves an RTP")
@allure.title("RTP is successfully retrieved")
@allure.tag("functional", "happy_path", "rtp_get")
@pytest.mark.get
@pytest.mark.happy_path
def test_get_rtp_success(debtor_service_provider_token_a, creditor_service_provider_token_a, rtp_reader_access_token):

    rtp_data = generate_rtp_data()

    activation_response = activate(
        debtor_service_provider_token_a,
        rtp_data["payer"]["payerId"],
        secrets.debtor_service_provider.service_provider_id,
    )

    assert activation_response.status_code == 201, "Error activating debtor"

    send_response = send_rtp(access_token=creditor_service_provider_token_a, rtp_payload=rtp_data)

    assert send_response.status_code == 201

    location = send_response.headers["Location"]
    resource_id = location.split("/")[-1]

    get_response = get_rtp(access_token=rtp_reader_access_token, rtp_id=resource_id)

    assert get_response.status_code == 200
    body = get_response.json()
    assert body["resourceID"] == resource_id


@allure.epic("RTP Get")
@allure.feature("RTP Get")
@allure.story("Service provider retrieves an RTP")
@allure.title("inexistent RTP -> empty body")
@allure.tag("functional", "unhappy_path", "rtp_get")
@pytest.mark.get
@pytest.mark.unhappy_path
def test_get_rtp_not_found(rtp_reader_access_token):

    fake_rtp_id = str(uuid.uuid4())

    resp = get_rtp(access_token=rtp_reader_access_token, rtp_id=fake_rtp_id)

    assert resp.status_code in (
        404,
        204,
    ), f"Status code: {resp.status_code}, body: {resp.text}"

    if resp.status_code == 204:
        assert resp.text == ""
    else:
        assert resp.text == "" or resp.json() == {}


@allure.epic("RTP Get")
@allure.feature("RTP Get")
@allure.story("Service provider retrieves an RTP")
@allure.title("malformed rtp_id → 400 Bad Request")
@allure.tag("functional", "unhappy_path", "rtp_get")
@pytest.mark.get
@pytest.mark.unhappy_path
def test_get_rtp_invalid_id_format(creditor_service_provider_token_a):

    bad_id = "123-not-a-uuid"
    resp = get_rtp(access_token=creditor_service_provider_token_a, rtp_id=bad_id)
    assert resp.status_code == 400, f"Atteso 400, ottenuto {resp.status_code}"


@allure.feature("RTP Get")
@allure.story("Service provider retrieves an RTP")
@allure.title("missing token → 401 Unauthorized")
@pytest.mark.get
@pytest.mark.unhappy_path
def test_get_rtp_missing_token():

    from uuid import uuid4

    fake_rtp = str(uuid4())

    resp = get_rtp(access_token="", rtp_id=fake_rtp)
    assert resp.status_code == 401

@allure.feature("RTP Get")
@allure.story("Come Sp Voglio sapere quali sono gli enti che hanno fatto Opt-out da RTP")
@allure.title("200 ok")
@pytest.mark.get
@pytest.mark.mock
@pytest.mark.happy_path
def test_get_rtp_optout_payees_list_mock():
   
   #Controllo che il codice HTTP della risposta sia 200 come atteso
   response = get_rtp_optout_payees_list_mock()
   assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

   #Controllo che il body della risposta sia una lista non vuota
   body = response.json()
   assert isinstance(body, list), f"Expected a list, got {type(body)}"
   assert len(body) > 0, f"Expected a non-empty list of opt-out payees"

   #Controllo che ogni elemento della lista abbia i campi 'payeeId', 'payeeName' e 'optOut_Flag' non vuoti e che 'optOut_Flag' sia True
   for payee in body:
       assert "payeeId" in payee, f"Missing 'payeeId' in payee: {payee}"
       assert "payeeName" in payee, f"Missing 'payeeName' in payee: {payee}"
       assert "optOut_Flag" in payee, f"Missing 'optOut_Flag' in payee: {payee}"
       assert payee["optOut_Flag"] is True,  f"'optOut_Flag' should be True in payee: {payee}, instead got {payee['optOut_Flag']}"
       
   
@allure.feature("RTP Get")
@allure.story("Come Sp Voglio sapere quali sono gli enti che hanno fatto Opt-out da RTP")
@allure.title("200 ok")
@pytest.mark.get
@pytest.mark.backoffice
@pytest.mark.happy_path
def test_get_rtp_optout_payees_list_backoffice():
   
   #Controllo che il codice HTTP della risposta sia 200 come atteso
   response = get_institutions_service_consent_backoffice_optout()
   assert response.status_code == 200, f"Expected status code 200, got {response.status_code}, body: {response.text}"

   #Controllo che il body della risposta sia una lista 
   body = response.json()
   assert isinstance(body, dict), f"Expected a dict, got {type(body)}"

   assert "results" in body, f"La chiave 'results' (o simile) non è presente nel dizionario"
    
   payees_list = body["results"] 
   assert isinstance(payees_list, list), f"Il contenuto di 'results' dovrebbe essere una lista"

    #  Controllo i campi di ogni elemento della lista
   for payee in payees_list:
        
        # Controllo consentInfo
        assert "consentInfo" in payee, f"Missing 'consentInfo' in payee: {payee}"
        assert "consent" in payee["consentInfo"], f"Missing 'consent' in consentInfo: {payee['consentInfo']}"
        
        # Estraggo il valore e lo confronto con OPT_OUT
        valore_consent = payee["consentInfo"]["consent"]
        assert valore_consent == "OPT_OUT", f"'consent' should be 'OPT_OUT', instead got {valore_consent}"
        
        # Controllo institutionInfo
        assert "institutionInfo" in payee, f"Missing 'institutionInfo' in payee: {payee}"
        assert "taxCode" in payee["institutionInfo"], f"Missing 'taxCode' in institutionInfo: {payee['institutionInfo']}"
        assert "name" in payee["institutionInfo"], f"Missing 'name' in institutionInfo: {payee['institutionInfo']}"
       
       
@allure.feature("RTP Get")
@allure.story("Come Sp Voglio sapere quali sono gli enti che hanno fatto Opt-out da RTP")
@allure.title("confronto tra lista opt-out e opt-in backoffice")
@pytest.mark.get
@pytest.mark.get
@pytest.mark.unhappy_path
def test_get_rtp_optout_payees_list_confront_with_optin_list_backoffice():
   
   #Controllo che il codice HTTP della risposta sia 200 come atteso
   response_optout = get_institutions_service_consent_backoffice_optout()
   assert response_optout.status_code == 200, f"Expected status code 200, got {response_optout.status_code}, body: {response_optout.text}"
   
   #Controllo che il codice HTTP della risposta sia 200 come atteso
   response_optin = get_institutions_service_consent_backoffice_optin()
   assert response_optin.status_code == 200, f"Expected status code 200, got {response_optin.status_code}, body: {response_optin.text}"

   #Estraggo le liste di payee opt-out e opt-in
   body_optout = response_optout.json()
   body_optin = response_optin.json()

   payees_optout_list = body_optout["results"]
   payees_optin_list = body_optin["results"]

   #Confronto le liste di payee opt-out e opt-in per verificare che non ci siano sovrapposizioni: gli enti che hanno fatto opt-out non dovrebbero essere presenti nella lista di quelli che hanno fatto opt-in
   tax_codes_optout = {payee["institutionInfo"]["taxCode"] for payee in payees_optout_list}
   tax_codes_optin = {payee["institutionInfo"]["taxCode"] for payee in payees_optin_list}
   sovrapposizioni = tax_codes_optout.intersection(tax_codes_optin)
   assert len(sovrapposizioni) == 0, f"Sono presenti sovrapposizioni tra enti opt-out e opt-in: {sovrapposizioni}"

@allure.feature("RTP Get")
@allure.story("Come Sp Voglio sapere quali sono gli enti che hanno fatto Opt-out da RTP")
@allure.title("200 ok")
@pytest.mark.get
@pytest.mark.happy_path
def test_get_payees_consents_optout(pagopa_payee_registry_token: str): 
   
   response =  get_payees_consents_optout(access_token=pagopa_payee_registry_token)
   assert response.status_code == 200, f"Expected status code 200, got {response.status_code}, body: {response.text}"

   body = response.json()
   assert isinstance(body, dict), f"Expected a dict, got {type(body)}"

   for payee in body.get("payees", []):
       assert "taxCode" in payee, f"Missing 'taxCode' in payee: {payee}"
       assert "name" in payee, f"Missing 'name' in payee: {payee}"
       
   