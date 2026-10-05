import allure
import pytest

from api.utils.endpoints import CALLBACK_URL_V2
from utils.dataset_callback_data_DS_08P_positive_v2 import generate_callback_data_DS_08P_positive_compliant
from utils.srtp_signature import sign_srtp_message, verify_srtp_message

SIGNING_HEADERS = {"Content-Type": "application/json"}


@allure.epic("QSealC message signing")
@allure.feature("Signature verification")
@allure.story("Verify a trusted certificate chain")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_verify_srtp_message_accepts_a_signature_with_a_trusted_root(
    qsealc_test_chain,
    ds_08p_callback_payload,
    callback_body_factory,
) -> None:
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
    ds_08p_callback_payload,
    callback_body_factory,
) -> None:
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

    result = verify_srtp_message(
        method="POST",
        url=CALLBACK_URL_V2,
        headers={**SIGNING_HEADERS, **signature.as_headers()},
        body=body,
        trusted_roots=(qsealc_key_material.certificate_pem,),
    )

    assert not result.is_valid, "Expected an untrusted certificate chain to be rejected"
    assert result.failure_reason == "UNTRUSTED_ISSUER", "Expected a trust-chain validation failure"
