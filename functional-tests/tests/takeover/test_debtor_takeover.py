import time
import uuid
from datetime import UTC, datetime

import allure
import pytest

from api.debtor_activation_api import activate, get_activation_by_id, get_activation_by_payer_id
from api.debtor_takeover_api import send_takeover_notification, takeover_activation
from config.configuration import secrets
from utils.activation_error_codes import ActivationErrorCode
from utils.activation_helpers import activate_with_sp_a, activate_with_sp_b
from utils.http_utils import extract_id_from_location


@allure.epic("Debtor Takeover")
@allure.feature("Takeover happy path")
@allure.title("Test Takeover Flow")
@allure.story("Takeover")
@allure.tag("functional", "happy_path", "activation", "takeover")
@pytest.mark.functional
@pytest.mark.happy_path
def test_takeover_flow(random_fiscal_code, debtor_service_provider_token_a, debtor_service_provider_token_b):
    """Test the takeover flow where a user changes service provider"""

    activation_response = activate_with_sp_a(debtor_service_provider_token_a, random_fiscal_code)
    assert activation_response.status_code == 201, (
        f"Failed to activate user with service provider A: {activation_response.text}"
    )

    activation_id = extract_id_from_location(activation_response.headers.get("Location"))
    assert activation_id is not None, "Activation ID is missing in Location header"

    get_response = get_activation_by_payer_id(debtor_service_provider_token_a, random_fiscal_code)
    assert get_response.status_code == 200, f"Failed to get user activation: {get_response.text}"

    current_sp = get_response.json()["payer"]["rtpSpId"]
    assert current_sp == secrets.debtor_service_provider.service_provider_id, (
        f"Expected service provider {secrets.debtor_service_provider.service_provider_id}, got {current_sp}"
    )

    second_activation_response = activate_with_sp_b(debtor_service_provider_token_b, random_fiscal_code)
    assert second_activation_response.status_code == 409, (
        f"Expected 409 conflict, got {second_activation_response.status_code}"
    )

    otp = extract_id_from_location(second_activation_response.headers.get("Location"))
    assert otp is not None, "Missing Location header in 409 response"

    takeover_response = takeover_activation(
        debtor_service_provider_token_b,
        random_fiscal_code,
        secrets.debtor_service_provider_B.service_provider_id,
        otp,
    )

    assert takeover_response.status_code == 201, f"Failed to takeover: {takeover_response.text}"

    new_activation_id = extract_id_from_location(takeover_response.headers.get("Location"))
    assert new_activation_id is not None, "Missing Location header in takeover response"

    time.sleep(1)

    get_after_takeover = get_activation_by_id(debtor_service_provider_token_b, new_activation_id)
    assert get_after_takeover.status_code == 200, f"Failed to get activation after takeover: {get_after_takeover.text}"

    new_sp = get_after_takeover.json()["payer"]["rtpSpId"]
    assert new_sp == secrets.debtor_service_provider_B.service_provider_id, (
        f"Takeover failed. Expected service provider {secrets.debtor_service_provider_B.service_provider_id}, got {new_sp}"
    )


@allure.epic("Debtor Takeover")
@allure.feature("Takeover happy path")
@allure.title("Test Takeover Redemption Assigns the OTP's Owned Service Provider ID")
@allure.story("Takeover redemption using a Service Provider ID owned but not represented by the redeemer")
@allure.tag("functional", "happy_path", "activation", "takeover", "ownership")
@pytest.mark.functional
@pytest.mark.happy_path
def test_takeover_redemption_assigns_otp_owned_service_provider_id(random_fiscal_code, debtor_service_provider_token_a):
    """MOCKSP04 owns both its own spId and MOCKSP01; redeeming an OTP scoped to MOCKSP01 must
    assign MOCKSP01 to the new activation, not MOCKSP04 (the redeemer's own tspId)."""

    owned_alt_sp_id = "MOCKSP01"
    bait_response = activate(
        debtor_service_provider_token_a, random_fiscal_code, secrets.debtor_service_provider.service_provider_id
    )
    assert bait_response.status_code == 201, f"Error activating bait debtor: {bait_response.text}"

    conflict_response = activate(debtor_service_provider_token_a, random_fiscal_code, owned_alt_sp_id)
    assert conflict_response.status_code == 409, (
        f"Expected 409 conflict (takeover trigger), got {conflict_response.status_code}: {conflict_response.text}"
    )
    otp = extract_id_from_location(conflict_response.headers.get("Location"))
    assert otp is not None, "Missing/invalid Location header (expected OTP for takeover trigger)"

    takeover_response = takeover_activation(debtor_service_provider_token_a, random_fiscal_code, owned_alt_sp_id, otp)
    assert takeover_response.status_code == 201, f"Failed to takeover: {takeover_response.text}"
    new_activation_id = extract_id_from_location(takeover_response.headers.get("Location"))
    assert new_activation_id is not None, "Missing Location header in takeover response"

    time.sleep(1)

    get_after_takeover = get_activation_by_id(debtor_service_provider_token_a, new_activation_id)
    assert get_after_takeover.status_code == 200, f"Failed to get activation after takeover: {get_after_takeover.text}"
    assert get_after_takeover.json()["payer"]["rtpSpId"] == owned_alt_sp_id, (
        "Takeover must assign the OTP's owned Service Provider ID, not the redeemer's own tspId"
    )


@allure.epic("Debtor Takeover")
@allure.feature("Takeover happy path")
@allure.title("Test Takeover Notification Endpoint")
@allure.story("Takeover Notification")
@pytest.mark.functional
@allure.tag("functional", "happy_path", "activation", "takeover")
@pytest.mark.happy_path
def test_takeover_notification(random_fiscal_code):
    """Availability probe for takeover notification mock endpoint: expects 204 No Content"""
    old_activation_id = str(uuid.uuid4())
    takeover_ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    resp = send_takeover_notification(
        old_activation_id=old_activation_id,
        fiscal_code=random_fiscal_code,
        takeover_timestamp=takeover_ts,
    )

    assert resp.status_code == 204, (
        f"Expected 204 from takeover notification mock, got {resp.status_code} - {resp.text} - url={getattr(resp.request, 'url', '')}"
    )
    assert not resp.text, "Expected empty body for 204 No Content response"


@allure.epic("Debtor Takeover")
@allure.feature("Takeover unhappy path")
@allure.title("Test Takeover Fails with Invalid OTP")
@allure.story("Takeover fails because of valid OTP")
@pytest.mark.functional
@allure.tag("functional", "unhappy_path", "activation", "takeover")
@pytest.mark.unhappy_path
def test_takeover_fails_invalid_otp(
    random_fiscal_code, debtor_service_provider_token_a, debtor_service_provider_token_b
):
    """Test that takeover fails when an invalid OTP is provided"""

    activation_response = activate_with_sp_a(debtor_service_provider_token_a, random_fiscal_code)
    assert activation_response.status_code == 201, (
        f"Failed to activate user with service provider A: {activation_response.text}"
    )

    second_activation_response = activate_with_sp_b(debtor_service_provider_token_b, random_fiscal_code)
    assert second_activation_response.status_code == 409, (
        f"Expected 409 conflict, got {second_activation_response.status_code}"
    )

    location_header = second_activation_response.headers.get("Location")
    assert location_header is not None, "Missing Location header in 409 response"

    invalid_otp = "invalid-otp-12345"
    takeover_response = takeover_activation(
        debtor_service_provider_token_b,
        random_fiscal_code,
        secrets.debtor_service_provider_B.service_provider_id,
        invalid_otp,
    )

    assert takeover_response.status_code == 400, (
        f"Expected 400 Bad Request for invalid OTP, got {takeover_response.status_code}"
    )


@allure.epic("Debtor Takeover")
@allure.feature("Takeover unhappy path")
@allure.title("Test Takeover Fails with Unauthenticated SP")
@allure.story("Takeover fails because of unauthenticated SP")
@pytest.mark.functional
@allure.tag("functional", "unhappy_path", "activation", "takeover")
@pytest.mark.unhappy_path
def test_takeover_with_unauthenticated_sp(
    random_fiscal_code, debtor_service_provider_token_a, debtor_service_provider_token_b
):
    """Test that takeover fails when the service provider is unauthenticated"""

    activation_response = activate_with_sp_a(debtor_service_provider_token_a, random_fiscal_code)
    assert activation_response.status_code == 201, (
        f"Failed to activate user with service provider A: {activation_response.text}"
    )

    second_activation_response = activate_with_sp_b(debtor_service_provider_token_b, random_fiscal_code)
    assert second_activation_response.status_code == 409, (
        f"Expected 409 conflict, got {second_activation_response.status_code}"
    )

    otp = extract_id_from_location(second_activation_response.headers.get("Location"))
    assert otp is not None, "Missing Location header in 409 response"

    takeover_response = takeover_activation(
        "",
        random_fiscal_code,
        secrets.debtor_service_provider_B.service_provider_id,
        otp,
    )

    assert takeover_response.status_code == 401, (
        f"Expected 401 Unauthorized for unauthenticated SP, got {takeover_response.status_code}"
    )


@allure.epic("Debtor Takeover")
@allure.feature("Takeover unhappy path")
@allure.title("Test Takeover Fails with OTP Bound to Different Payer")
@allure.story("Takeover fails because of OTP bound to different payer")
@pytest.mark.functional
@allure.tag("functional", "unhappy_path", "activation", "takeover")
@pytest.mark.unhappy_path
def test_takeover_otp_for_different_payer_fails(
    random_fiscal_code, debtor_service_provider_token_a, debtor_service_provider_token_b
):
    """OTP bound to payer1 should not work for payer2"""
    payer1 = random_fiscal_code
    assert activate_with_sp_a(debtor_service_provider_token_a, payer1).status_code == 201

    resp = activate_with_sp_b(debtor_service_provider_token_b, payer1)
    assert resp.status_code == 409
    otp = extract_id_from_location(resp.headers.get("Location"))
    assert otp is not None, "Missing Location header in 409 response"

    bad = takeover_activation(
        debtor_service_provider_token_a,
        random_fiscal_code,
        secrets.debtor_service_provider_B.service_provider_id,
        otp,
    )
    assert bad.status_code == 403, f"Expected 403 for OTP bound to another payer, got {bad.status_code}: {bad.text}"


@allure.epic("Debtor Takeover")
@allure.feature("Takeover unhappy path")
@allure.title("Test Takeover Fails without Prior OTP")
@allure.story("Takeover fails because of missing OTP")
@pytest.mark.functional
@allure.tag("functional", "unhappy_path", "activation", "takeover")
@pytest.mark.unhappy_path
def test_takeover_without_prior_otp_fails(
    random_fiscal_code, debtor_service_provider_token_a, debtor_service_provider_token_b
):
    """Takeover without a previously issued OTP should fail"""
    assert activate_with_sp_a(debtor_service_provider_token_a, random_fiscal_code).status_code == 201

    fake_otp = str(uuid.uuid4())
    resp = takeover_activation(
        debtor_service_provider_token_b,
        random_fiscal_code,
        secrets.debtor_service_provider_B.service_provider_id,
        fake_otp,
    )
    assert resp.status_code == 401, (
        f"Expected 401 for takeover without OTP issuance, got {resp.status_code}: {resp.text}"
    )


@allure.epic("Debtor Takeover")
@allure.feature("Takeover unhappy path")
@allure.title("Test Takeover Fails with Empty OTP")
@allure.story("Takeover fails because of empty OTP")
@pytest.mark.functional
@allure.tag("functional", "unhappy_path", "activation", "takeover")
@pytest.mark.unhappy_path
def test_takeover_empty_otp_bad_request(
    random_fiscal_code, debtor_service_provider_token_a, debtor_service_provider_token_b
):
    """Empty OTP should be rejected"""
    assert activate_with_sp_a(debtor_service_provider_token_a, random_fiscal_code).status_code == 201

    with pytest.raises(ValueError, match="OTP is required"):
        takeover_activation(
            debtor_service_provider_token_b,
            random_fiscal_code,
            secrets.debtor_service_provider_B.service_provider_id,
            "",
        )


@allure.epic("Debtor Takeover")
@allure.feature("Takeover unhappy path")
@allure.title("Test Takeover Fails with Wrong SP Token")
@allure.story("Takeover fails because of wrong SP token")
@pytest.mark.functional
@allure.tag("functional", "unhappy_path", "activation", "takeover")
@pytest.mark.unhappy_path
def test_takeover_with_token_of_wrong_sp_forbidden(
    random_fiscal_code, debtor_service_provider_token_a, debtor_service_provider_token_b
):
    """Authenticated but not authorized: token of SP A tries to use OTP issued for SP B"""
    assert activate_with_sp_a(debtor_service_provider_token_a, random_fiscal_code).status_code == 201

    resp = activate_with_sp_b(debtor_service_provider_token_b, random_fiscal_code)
    assert resp.status_code == 409
    otp = extract_id_from_location(resp.headers.get("Location"))
    assert otp is not None, "Missing Location header in 409 response"

    forbidden = takeover_activation(
        debtor_service_provider_token_a,
        random_fiscal_code,
        secrets.debtor_service_provider_B.service_provider_id,
        otp,
    )
    assert forbidden.status_code == 403, f"Expected 403 Forbidden, got {forbidden.status_code}: {forbidden.text}"


@allure.epic("Debtor Takeover")
@allure.feature("Takeover unhappy path")
@allure.title("Test Takeover Fails with Reused OTP")
@allure.story("Takeover fails because of reused OTP")
@pytest.mark.functional
@allure.tag("functional", "unhappy_path", "activation", "takeover")
@pytest.mark.unhappy_path
def test_takeover_reuse_otp_fails(random_fiscal_code, debtor_service_provider_token_a, debtor_service_provider_token_b):
    """Reusing the same OTP after a successful takeover should fail"""
    activation_response = activate_with_sp_a(debtor_service_provider_token_a, random_fiscal_code)
    assert activation_response.status_code == 201

    second_activation_response = activate_with_sp_b(debtor_service_provider_token_b, random_fiscal_code)
    assert second_activation_response.status_code == 409

    otp = extract_id_from_location(second_activation_response.headers.get("Location"))
    assert otp is not None, "Missing Location header in 409 response"

    takeover_response = takeover_activation(
        debtor_service_provider_token_b,
        random_fiscal_code,
        secrets.debtor_service_provider_B.service_provider_id,
        otp,
    )
    assert takeover_response.status_code == 201

    retry = takeover_activation(
        debtor_service_provider_token_b,
        random_fiscal_code,
        secrets.debtor_service_provider_B.service_provider_id,
        otp,
    )
    assert retry.status_code == 401, f"Expected 401 on OTP reuse, got {retry.status_code}: {retry.text}"


@allure.epic("Debtor Takeover")
@allure.feature("Takeover unhappy path")
@allure.title("Test Takeover Fails with Nonsensical Body")
@allure.story("Takeover fails because of nonsensical body")
@pytest.mark.functional
@allure.tag("functional", "unhappy_path", "activation", "takeover")
@pytest.mark.unhappy_path
def test_takeover_no_sense_body_but_valid_syntax(
    random_fiscal_code, debtor_service_provider_token_a, debtor_service_provider_token_b
):
    """Takeover with syntactically valid but nonsensical body should fail"""
    assert activate_with_sp_a(debtor_service_provider_token_a, random_fiscal_code).status_code == 201

    resp = activate_with_sp_b(debtor_service_provider_token_b, random_fiscal_code)
    assert resp.status_code == 409
    otp = extract_id_from_location(resp.headers.get("Location"))
    assert otp is not None, "Missing Location header in 409 response"

    bad = takeover_activation(
        debtor_service_provider_token_b,
        random_fiscal_code,
        secrets.debtor_service_provider_B.service_provider_id,
        otp,
        include_payload=True,
    )
    assert bad.status_code == 400, f"Expected 400 for nonsensical body, got {bad.status_code}: {bad.text}"


@allure.epic("Debtor Takeover")
@allure.feature("Takeover unhappy path")
@allure.title("Test Takeover Fails when Redeemer Does Not Own the OTP's Service Provider ID")
@allure.story("Takeover fails because the redeemer does not own the OTP's Service Provider ID")
@pytest.mark.functional
@allure.tag("functional", "unhappy_path", "activation", "takeover", "ownership")
@pytest.mark.unhappy_path
def test_takeover_redeemer_not_owning_otp_service_provider_id_forbidden(
    random_fiscal_code, debtor_service_provider_token_a, debtor_service_provider_token_b
):
    """MOCKSP04 owns MOCKSP01 and triggers the OTP; FAKESP01, which owns neither, must be rejected
    with an explicit ownership error, not merely a generic 403."""

    owned_alt_sp_id = "MOCKSP01"
    bait_response = activate(
        debtor_service_provider_token_a, random_fiscal_code, secrets.debtor_service_provider.service_provider_id
    )
    assert bait_response.status_code == 201, f"Error activating bait debtor: {bait_response.text}"

    conflict_response = activate(debtor_service_provider_token_a, random_fiscal_code, owned_alt_sp_id)
    assert conflict_response.status_code == 409, (
        f"Expected 409 conflict (takeover trigger), got {conflict_response.status_code}: {conflict_response.text}"
    )
    otp = extract_id_from_location(conflict_response.headers.get("Location"))
    assert otp is not None, "Missing/invalid Location header (expected OTP for takeover trigger)"

    res = takeover_activation(debtor_service_provider_token_b, random_fiscal_code, owned_alt_sp_id, otp)
    assert res.status_code == 403, f"Expected 403 Forbidden, got {res.status_code}: {res.text}"
    assert res.json()["errors"][0]["code"] == ActivationErrorCode.SERVICE_PROVIDER_ID_NOT_OWNED.code
    assert res.json()["errors"][0]["description"] == ActivationErrorCode.SERVICE_PROVIDER_ID_NOT_OWNED.description
