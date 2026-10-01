"""Test QSealC signature, trust-chain, validity, and revocation verification."""

import base64
from datetime import timedelta

import allure
import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.padding import MGF1, PSS

from api.utils.endpoints import CALLBACK_URL_V2
from utils.dataset_callback_data_DS_08P_positive_v2 import generate_callback_data_DS_08P_positive_compliant
from utils.srtp_message_signing import build_canonical_representation
from utils.srtp_signature import (
    RevocationResult,
    RevocationStatus,
    sign_srtp_message,
    verify_srtp_message,
)

SIGNING_HEADERS = {"Content-Type": "application/json"}


@allure.epic("QSealC message signing")
@allure.feature("Signature verification")
@allure.story("Verify a trusted certificate chain")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_verify_srtp_message_accepts_a_signature_with_a_trusted_root(
    qsealc_test_chain,
    signed_callback_message,
) -> None:
    """Accept a signature whose chain terminates at a trusted root."""
    body, signature = signed_callback_message

    result = verify_srtp_message(
        method="POST",
        url=CALLBACK_URL_V2,
        headers={**SIGNING_HEADERS, **signature.as_headers()},
        body=body,
        trusted_roots=(qsealc_test_chain.root_certificate_pem,),
    )

    assert result.is_valid, f"Expected the trusted signature to verify: {result.failure_detail}"
    assert result.validated_certificate_chain_length == 2, (
        "Expected the leaf and trusted root certificates to form the validated chain"
    )


@allure.epic("QSealC message signing")
@allure.feature("Signature verification")
@allure.story("Reject a changed message body")
@pytest.mark.functional
@pytest.mark.unhappy_path
@pytest.mark.callback
def test_verify_srtp_message_rejects_a_signature_for_changed_body(
    qsealc_test_chain,
    ds_08p_callback_payload,
    callback_body_factory,
) -> None:
    """Reject a signature after the canonicalized body has changed."""
    body = callback_body_factory(
        method="POST",
        url=CALLBACK_URL_V2,
        payload=ds_08p_callback_payload,
    )
    signature = sign_srtp_message(
        method="POST",
        url=CALLBACK_URL_V2,
        headers=SIGNING_HEADERS,
        body=body,
        key_material=qsealc_test_chain.key_material,
    )
    changed_body = callback_body_factory(
        method="POST",
        url=CALLBACK_URL_V2,
        payload=generate_callback_data_DS_08P_positive_compliant(),
    )

    result = verify_srtp_message(
        method="POST",
        url=CALLBACK_URL_V2,
        headers={**SIGNING_HEADERS, **signature.as_headers()},
        body=changed_body,
        trusted_roots=(qsealc_test_chain.root_certificate_pem,),
    )

    assert not result.is_valid, "Expected the signature to fail after the body changed"
    assert result.failure_reason == "INVALID_SIGNATURE", "Expected a canonical body mismatch failure"


@allure.epic("QSealC message signing")
@allure.feature("Signature verification")
@allure.story("Reject a certificate chain without a trusted root")
@pytest.mark.functional
@pytest.mark.unhappy_path
@pytest.mark.callback
def test_verify_srtp_message_rejects_an_untrusted_certificate_chain(
    qsealc_test_chain,
    qsealc_key_material,
    signed_callback_message,
) -> None:
    """Reject a valid signature whose certificate chain is untrusted."""
    body, signature = signed_callback_message

    result = verify_srtp_message(
        method="POST",
        url=CALLBACK_URL_V2,
        headers={**SIGNING_HEADERS, **signature.as_headers()},
        body=body,
        trusted_roots=(qsealc_key_material.certificate_pem,),
    )

    assert not result.is_valid, "Expected an untrusted certificate chain to be rejected"
    assert result.failure_reason == "UNTRUSTED_ISSUER", "Expected a trust-chain validation failure"


@allure.epic("QSealC message signing")
@allure.feature("Signature verification")
@allure.story("Reject an expired certificate")
@pytest.mark.functional
@pytest.mark.unhappy_path
@pytest.mark.callback
def test_verify_srtp_message_rejects_an_expired_certificate(
    qsealc_test_chain,
    signed_callback_message,
) -> None:
    """Reject a signature whose certificate chain is expired."""
    body, signature = signed_callback_message

    result = verify_srtp_message(
        method="POST",
        url=CALLBACK_URL_V2,
        headers={**SIGNING_HEADERS, **signature.as_headers()},
        body=body,
        trusted_roots=(qsealc_test_chain.root_certificate_pem,),
        at_time=qsealc_test_chain.valid_until + timedelta(minutes=1),
    )

    assert not result.is_valid, "Expected an expired certificate to be rejected"
    assert result.failure_reason == "CERTIFICATE_EXPIRED", "Expected a certificate validity failure"


@allure.epic("QSealC message signing")
@allure.feature("Signature verification")
@allure.story("Reject a revoked certificate")
@pytest.mark.functional
@pytest.mark.unhappy_path
@pytest.mark.callback
def test_verify_srtp_message_rejects_a_revoked_certificate(
    qsealc_test_chain,
    signed_callback_message,
) -> None:
    """Reject a signature when the revocation checker reports revoked."""
    body, signature = signed_callback_message

    result = verify_srtp_message(
        method="POST",
        url=CALLBACK_URL_V2,
        headers={**SIGNING_HEADERS, **signature.as_headers()},
        body=body,
        trusted_roots=(qsealc_test_chain.root_certificate_pem,),
        revocation_checker=lambda _certificate, _issuer: RevocationResult(
            status=RevocationStatus.REVOKED,
            source="test",
            reason="Certificate serial number is listed as revoked",
        ),
    )

    assert not result.is_valid, "Expected a revoked certificate to be rejected"
    assert result.failure_reason == "CERTIFICATE_REVOKED", "Expected a revocation failure"
    assert result.revocation_status is RevocationStatus.REVOKED, "Expected the revoked status to be preserved"


@allure.epic("QSealC message signing")
@allure.feature("Signature verification")
@allure.story("Report an unknown certificate revocation status")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_verify_srtp_message_reports_an_unknown_revocation_status(
    qsealc_test_chain,
    signed_callback_message,
) -> None:
    """Preserve an unknown revocation status without rejecting the signature."""
    body, signature = signed_callback_message

    result = verify_srtp_message(
        method="POST",
        url=CALLBACK_URL_V2,
        headers={**SIGNING_HEADERS, **signature.as_headers()},
        body=body,
        trusted_roots=(qsealc_test_chain.root_certificate_pem,),
        revocation_checker=lambda _certificate, _issuer: RevocationResult(
            status=RevocationStatus.UNKNOWN,
            source="test",
        ),
    )

    assert result.is_valid, f"Expected signature verification to succeed: {result.failure_detail}"
    assert result.revocation_status is RevocationStatus.UNKNOWN, "Expected the unknown status to be preserved"


@allure.epic("QSealC message signing")
@allure.feature("Signature verification")
@allure.story("Accept RSA-PSS signatures")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
@pytest.mark.parametrize(
    ("salt_length", "salt_label"),
    (
        (PSS.DIGEST_LENGTH, "digest-length"),
        (PSS.MAX_LENGTH, "maximum-length"),
    ),
    ids=("digest-length", "maximum-length"),
)
def test_verify_srtp_message_accepts_rsa_pss_signatures(
    qsealc_test_chain,
    signed_callback_message,
    salt_length,
    salt_label,
) -> None:
    """Accept RSA-PSS signatures using supported salt-length conventions."""
    body, signed_message = signed_callback_message
    canonical = build_canonical_representation(
        method="POST",
        url=CALLBACK_URL_V2,
        headers=SIGNING_HEADERS,
        body=body,
    )
    pss_signature = qsealc_test_chain.key_material.private_key.sign(
        data=canonical,
        padding=PSS(mgf=MGF1(hashes.SHA256()), salt_length=salt_length),
        algorithm=hashes.SHA256(),
    )
    headers = {
        **SIGNING_HEADERS,
        **signed_message.as_headers(),
        "X-SRTP-Signature": base64.b64encode(pss_signature).decode("ascii"),
    }

    result = verify_srtp_message(
        method="POST",
        url=CALLBACK_URL_V2,
        headers=headers,
        body=body,
        trusted_roots=(qsealc_test_chain.root_certificate_pem,),
    )

    assert result.is_valid, f"Expected RSA-PSS ({salt_label}) verification to succeed: {result.failure_detail}"


@allure.epic("QSealC message signing")
@allure.feature("Signature verification")
@allure.story("Reject an invalid target URI")
@pytest.mark.functional
@pytest.mark.unhappy_path
@pytest.mark.callback
@pytest.mark.parametrize("invalid_url", ("/callback", "mailto:callback@example.com"))
def test_verify_srtp_message_rejects_an_invalid_target_uri(
    qsealc_test_chain,
    signed_callback_message,
    invalid_url,
) -> None:
    """Reject a message whose target URI cannot be canonicalized."""
    body, signed_message = signed_callback_message

    result = verify_srtp_message(
        method="POST",
        url=invalid_url,
        headers={**SIGNING_HEADERS, **signed_message.as_headers()},
        body=body,
        trusted_roots=(qsealc_test_chain.root_certificate_pem,),
    )

    assert not result.is_valid, "Expected an incomplete target URI to be rejected"
    assert result.failure_reason == "INVALID_MESSAGE", "Expected an invalid-message failure"
