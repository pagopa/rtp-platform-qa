"""Tests for the GET /activations/payer/{payerId}/status endpoint.

This endpoint returns a minimal yes/no response indicating whether a payer (identified
by fiscal code or VAT number) is currently active in the RTP system.
The ``payerId`` is passed as a **path parameter**.

Privacy rule: the response is deliberately indistinguishable between "not found" and
"active under a different Service Provider" — both cases return ``{ "isActive": false }``
— to avoid leaking cross-SP information to competitors.

Authorization roles:
- ``read_rtp_activations``: reads only activations whose ``serviceProviderDebtor`` matches
  the ``sub`` claim of the presented JWT.
- ``read_rtp_all``: reads activations for any Service Provider (admin-level visibility).

The ``INVALID_PAYER_IDS`` constant (from ``tests.payer_id_data``) drives the parametrized 400 suite.
It mirrors the ``invalidFiscalCodes`` data source in ``ActivationAPIControllerImplTest.java``
and is extended with structural edge cases from the Italian CF/PIVA specification:

- **Length boundaries**: too-short (14) and too-long (18) CFs; 10- and 12-digit VATs.
- **Case**: lowercase and mixed-case CFs (only uppercase alphanumeric is valid).
- **Month codes**: valid set is A B C D E H L M P R S T.  F and G (between valid E and H)
  and U (outside range) are the most common off-by-one mistakes.
- **Birth day**: male range 01–31, female range 41–71.  Day 00, 32, 40 (dead zone), and 72
  are the relevant boundary violations.
- **Special characters**: ``!``, embedded space, leading/trailing whitespace (17 chars → length
  error), non-numeric VAT-like string, all-zeros (10 digits).
- **EU VAT prefix**: ``IT`` + 11 digits → 13 chars → length error (common client mistake).
- **Checksum probe**: syntactically valid CF with wrong control character.  This case acts
  as a TDD sentinel: it stays red until the backend enforces checksum validation.
- **Empty string**: empty path segment → 400 (or 404 depending on routing).
"""

import allure
import pytest

from api.debtor_activation_api import get_activation_status_by_fiscal_code
from api.debtor_deactivation_api import deactivate
from utils.dataset_payer_id_invalid import INVALID_PAYER_IDS


@allure.epic("Debtor Activation")
@allure.feature("Payer Status")
@allure.story("Get Activation Status by Fiscal Code")
@allure.title("An active payer returns isActive true for the same Service Provider")
@allure.tag("functional", "happy_path", "activation", "payer_status")
@pytest.mark.activation
@pytest.mark.happy_path
def test_get_activation_status_active_payer(debtor_service_provider_token_a, make_activation):
    """Payer activated under SP A queried by SP A → isActive must be true."""
    _activation_id, debtor_fc = make_activation()
    res = get_activation_status_by_fiscal_code(debtor_service_provider_token_a, debtor_fc)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}: {res.text}"
    assert res.json()["isActive"] is True, f"Expected isActive=true but got: {res.json()}"


@allure.tag("functional", "happy_path", "activation", "payer_status")
@pytest.mark.activation
@pytest.mark.happy_path
def test_get_activation_status_not_active_payer(debtor_service_provider_token_a, random_fiscal_code):
    """Payer that has never been activated → isActive must be false."""
    res = get_activation_status_by_fiscal_code(debtor_service_provider_token_a, random_fiscal_code)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}: {res.text}"
    assert res.json()["isActive"] is False, f"Expected isActive=false but got: {res.json()}"


@allure.feature("Payer Status")
@allure.story("Get Activation Status by Fiscal Code")
@allure.title("A payer active on a different Service Provider returns isActive false (privacy)")
@allure.tag("functional", "happy_path", "activation", "payer_status")
@pytest.mark.activation
@pytest.mark.happy_path
def test_get_activation_status_active_payer_different_service_provider(
    debtor_service_provider_token_a, debtor_service_provider_token_b, make_activation
):
    """
    SP A activates the payer.
    SP B queries the status → must get isActive=false to avoid disclosing
    that the payer is registered under a competitor SP.
    """
    _activation_id, debtor_fc = make_activation()

    res = get_activation_status_by_fiscal_code(debtor_service_provider_token_b, debtor_fc)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}: {res.text}"
    assert res.json()["isActive"] is False, (
        f"Expected isActive=false for a different SP (privacy rule) but got: {res.json()}"
    )


@allure.epic("Debtor Activation")
@allure.feature("Payer Status")
@allure.story("Get Activation Status by Fiscal Code")
@allure.title("read_rtp_all role returns isActive true for a payer on any Service Provider")
@allure.tag("functional", "happy_path", "activation", "payer_status", "rbac")
@pytest.mark.activation
@pytest.mark.happy_path
def test_get_activation_status_read_rtp_all_role_own_service_provider(
    debtor_service_provider_token_a, sp_activations_read_all_token, make_activation
):
    """
    Payer activated under SP A.
    Token with read_rtp_all can read across all Service Providers:
    the admin client sub does not match SP A, yet isActive must be true.
    """
    _activation_id, debtor_fc = make_activation()

    res = get_activation_status_by_fiscal_code(sp_activations_read_all_token, debtor_fc)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}: {res.text}"
    assert res.json()["isActive"] is True, f"Expected isActive=true with read_rtp_all role but got: {res.json()}"


@allure.epic("Debtor Activation")
@allure.feature("Payer Status")
@allure.story("Get Activation Status by Fiscal Code")
@allure.title(
    "read_rtp_all role returns isActive true while read_rtp_activations returns false for the same cross-SP payer"
)
@allure.tag("functional", "happy_path", "activation", "payer_status", "rbac")
@pytest.mark.activation
@pytest.mark.happy_path
def test_get_activation_status_role_comparison_cross_service_provider(
    debtor_service_provider_token_b, sp_activations_read_all_token, make_activation
):
    """
    Payer activated under SP A.
    - SP B (read_rtp_activations): isActive must be false — privacy rule hides cross-SP activation.
    - Admin (read_rtp_all): isActive must be true — role grants visibility across all SPs.
    Same payer, same endpoint, different roles → different results.
    """
    _activation_id, debtor_fc = make_activation()

    res_sp_b = get_activation_status_by_fiscal_code(debtor_service_provider_token_b, debtor_fc)
    assert res_sp_b.status_code == 200, f"Expected 200 but got {res_sp_b.status_code}: {res_sp_b.text}"
    assert res_sp_b.json()["isActive"] is False, (
        f"read_rtp_activations (SP B): expected isActive=false for cross-SP payer but got: {res_sp_b.json()}"
    )

    res_admin = get_activation_status_by_fiscal_code(sp_activations_read_all_token, debtor_fc)
    assert res_admin.status_code == 200, f"Expected 200 but got {res_admin.status_code}: {res_admin.text}"
    assert res_admin.json()["isActive"] is True, (
        f"read_rtp_all (admin): expected isActive=true for cross-SP payer but got: {res_admin.json()}"
    )


@allure.epic("Debtor Activation")
@allure.feature("Payer Status")
@allure.story("Get Activation Status by Fiscal Code")
@allure.title("A deactivated payer returns isActive false")
@allure.tag("functional", "happy_path", "activation", "payer_status")
@pytest.mark.activation
@pytest.mark.happy_path
def test_get_activation_status_deactivated_payer(debtor_service_provider_token_a, make_activation):
    """Payer activated then deactivated by SP A → isActive must be false."""
    activation_id, debtor_fc = make_activation()

    deactivate_res = deactivate(debtor_service_provider_token_a, activation_id)
    assert deactivate_res.status_code == 204, (
        f"Deactivation failed: expected 204 but got {deactivate_res.status_code}: {deactivate_res.text}"
    )

    res = get_activation_status_by_fiscal_code(debtor_service_provider_token_a, debtor_fc)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}: {res.text}"
    assert res.json()["isActive"] is False, f"Expected isActive=false after deactivation but got: {res.json()}"


@allure.epic("Debtor Activation")
@allure.feature("Payer Status")
@allure.story("Get Activation Status by Fiscal Code")
@allure.title("An active payer with omocodia fiscal code returns isActive true")
@allure.tag("functional", "happy_path", "activation", "payer_status", "omocodia")
@pytest.mark.activation
@pytest.mark.happy_path
def test_get_activation_status_omocodia_fiscal_code(
    debtor_service_provider_token_a, make_activation, random_omocodia_fiscal_code
):
    """Active payer with omocodia fiscal code (digit substitution) → isActive must be true."""
    _activation_id, _ = make_activation(random_omocodia_fiscal_code)

    res = get_activation_status_by_fiscal_code(debtor_service_provider_token_a, random_omocodia_fiscal_code)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}: {res.text}"
    assert res.json()["isActive"] is True, f"Expected isActive=true for omocodia FC but got: {res.json()}"


@allure.epic("Debtor Activation")
@allure.feature("Payer Status")
@allure.story("Get Activation Status by Fiscal Code")
@allure.title("An active payer with foreign fiscal code returns isActive true")
@allure.tag("functional", "happy_path", "activation", "payer_status", "foreign")
@pytest.mark.activation
@pytest.mark.happy_path
def test_get_activation_status_foreign_fiscal_code(
    debtor_service_provider_token_a, make_activation, random_foreign_fiscal_code
):
    """Active payer with a foreign-country fiscal code (Z + 3 digits municipality) → isActive must be true."""
    _activation_id, _ = make_activation(random_foreign_fiscal_code)

    res = get_activation_status_by_fiscal_code(debtor_service_provider_token_a, random_foreign_fiscal_code)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}: {res.text}"
    assert res.json()["isActive"] is True, f"Expected isActive=true for foreign FC but got: {res.json()}"


@allure.epic("Debtor Activation")
@allure.feature("Payer Status")
@allure.story("Get Activation Status by Fiscal Code")
@allure.title("An active payer with VAT number (Partita IVA) returns isActive true")
@allure.tag("functional", "happy_path", "activation", "payer_status", "vat")
@pytest.mark.activation
@pytest.mark.happy_path
def test_get_activation_status_vat_number(debtor_service_provider_token_a, make_activation, random_vat_number):
    """Active payer identified by an 11-digit Partita IVA → isActive must be true."""
    _activation_id, _ = make_activation(random_vat_number)

    res = get_activation_status_by_fiscal_code(debtor_service_provider_token_a, random_vat_number)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}: {res.text}"
    assert res.json()["isActive"] is True, f"Expected isActive=true for VAT number but got: {res.json()}"


@allure.epic("Debtor Activation")
@allure.feature("Payer Status")
@allure.story("Get Activation Status by Fiscal Code")
@allure.title("Querying activation status without a valid token returns 401")
@allure.tag("functional", "unhappy_path", "activation", "payer_status")
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_activation_status_unauthorized():
    """Missing or invalid Bearer token → the endpoint must return 401."""
    fake_token = "Bearer invalid.token.value"
    res = get_activation_status_by_fiscal_code(fake_token, "RSSMRA85T10A562S")
    assert res.status_code == 401, f"Expected 401 but got {res.status_code}: {res.text}"


@allure.epic("Debtor Activation")
@allure.feature("Payer Status")
@allure.story("Get Activation Status by Fiscal Code")
@allure.title("Token without read_rtp_activation or read_rtp_all role returns 403 Forbidden")
@allure.tag("functional", "unhappy_path", "activation", "payer_status", "security")
@pytest.mark.activation
@pytest.mark.unhappy_path
def test_get_activation_status_forbidden_no_role(pagopa_service_providers_registry_token, random_fiscal_code):
    """A valid token that carries neither read_rtp_activations nor read_rtp_all must be rejected with 403."""
    res = get_activation_status_by_fiscal_code(pagopa_service_providers_registry_token, random_fiscal_code)
    assert res.status_code == 403, f"Expected 403 Forbidden but got {res.status_code}: {res.text}"


@allure.epic("Debtor Activation")
@allure.feature("Payer Status")
@allure.story("Get Activation Status by Fiscal Code")
@allure.title("Querying activation status with an invalid payerId format returns 400")
@allure.tag("functional", "unhappy_path", "activation", "payer_status")
@pytest.mark.activation
@pytest.mark.unhappy_path
@pytest.mark.parametrize("description,invalid_payer_id", INVALID_PAYER_IDS)
def test_get_activation_status_invalid_payer_id_format(debtor_service_provider_token_a, description, invalid_payer_id):
    """Each entry in ``INVALID_PAYER_IDS`` must be rejected with 400.

    The ``description`` parameter appears in pytest output to identify which
    case failed without having to inspect the raw value.
    """
    res = get_activation_status_by_fiscal_code(debtor_service_provider_token_a, invalid_payer_id)
    assert res.status_code == 400, f"[{description}] Expected 400 but got {res.status_code}: {res.text}"
