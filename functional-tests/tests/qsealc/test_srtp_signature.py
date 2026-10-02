"""Test QSealC signature generation and certificate-header encoding."""

import base64
import hashlib

import allure
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.serialization import Encoding

from api.utils.endpoints import CALLBACK_URL_V2
from utils.srtp_signature import (
    SRTP_CERTIFICATE_CHAIN_HEADER,
    SRTP_SIGNATURE_ALGORITHM_DIGEST_HEADER,
    SRTP_SIGNATURE_CERTIFICATE_HEADER,
    SRTP_SIGNATURE_HEADER,
    sign_srtp_message,
)

SIGNING_HEADERS = {"Content-Type": "application/json"}


@allure.epic("QSealC message signing")
@allure.feature("Signature generation")
@allure.story("Sign a canonical SRTP message")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_sign_srtp_message_returns_a_verifiable_signature_and_headers(
    qsealc_key_material,
    ds_08p_callback_payload,
    callback_body_factory,
) -> None:
    """Generate a verifiable signature and all required transport headers."""
    body = callback_body_factory(
        method="POST",
        url=CALLBACK_URL_V2,
        payload=ds_08p_callback_payload,
    )
    signed_message = sign_srtp_message(
        method="POST",
        url=CALLBACK_URL_V2,
        headers=SIGNING_HEADERS,
        body=body,
        key_material=qsealc_key_material,
    )
    canonical = b"POST\n" + CALLBACK_URL_V2.encode() + b"\ncontent-type: application/json\n" + body

    qsealc_key_material.private_key.public_key().verify(
        signature=base64.b64decode(signed_message.signature_base64),
        data=canonical,
        padding=PKCS1v15(),
        algorithm=hashes.SHA256(),
    )

    expected_digest = base64.b64encode(hashlib.sha256(canonical).digest()).decode()
    assert signed_message.digest_base64 == expected_digest, "Expected the digest of the canonical message"
    assert signed_message.as_headers() == {
        SRTP_SIGNATURE_HEADER: signed_message.signature_base64,
        SRTP_SIGNATURE_CERTIFICATE_HEADER: signed_message.certificate_base64,
        SRTP_CERTIFICATE_CHAIN_HEADER: signed_message.certificate_chain_base64,
        SRTP_SIGNATURE_ALGORITHM_DIGEST_HEADER: "sha256",
    }, "Expected all signature-related headers to be emitted"


@allure.epic("QSealC message signing")
@allure.feature("Signature generation")
@allure.story("Use an explicit digest algorithm")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
@pytest.mark.parametrize(
    ("algorithm", "hash_algorithm_type", "expected_algorithm", "hashlib_algorithm"),
    (
        ("SHA512", hashes.SHA512, "sha512", "sha512"),
        ("SHA3-256", hashes.SHA3_256, "sha3-256", "sha3-256"),
    ),
    ids=("sha512", "sha3-256"),
)
def test_sign_srtp_message_uses_an_explicit_digest_algorithm(
    qsealc_key_material,
    ds_08p_callback_payload,
    callback_body_factory,
    algorithm,
    hash_algorithm_type,
    expected_algorithm,
    hashlib_algorithm,
) -> None:
    """Generate signatures for each supported explicit digest algorithm."""
    body = callback_body_factory(
        method="POST",
        url=CALLBACK_URL_V2,
        payload=ds_08p_callback_payload,
    )
    signed_message = sign_srtp_message(
        method="POST",
        url=CALLBACK_URL_V2,
        headers=SIGNING_HEADERS,
        body=body,
        key_material=qsealc_key_material,
        algorithm=algorithm,
    )
    canonical = b"POST\n" + CALLBACK_URL_V2.encode() + b"\ncontent-type: application/json\n" + body

    qsealc_key_material.private_key.public_key().verify(
        signature=base64.b64decode(signed_message.signature_base64),
        data=canonical,
        padding=PKCS1v15(),
        algorithm=hash_algorithm_type(),
    )

    assert signed_message.algorithm == expected_algorithm, "Expected digest algorithm names to be normalized"
    assert signed_message.digest_base64 == base64.b64encode(
        hashlib.new(hashlib_algorithm, canonical).digest()
    ).decode(), "Expected the selected digest to cover the canonical message"
    assert signed_message.as_headers()[SRTP_SIGNATURE_ALGORITHM_DIGEST_HEADER] == expected_algorithm, (
        "Expected the selected digest algorithm to be advertised"
    )


@allure.epic("QSealC message signing")
@allure.feature("Signature generation")
@allure.story("Reject unsupported digest algorithms")
@pytest.mark.functional
@pytest.mark.unhappy_path
@pytest.mark.callback
def test_sign_srtp_message_rejects_unsupported_digest_algorithms(
    qsealc_key_material,
    ds_08p_callback_payload,
    callback_body_factory,
) -> None:
    """Reject digest algorithms outside the supported set."""
    body = callback_body_factory(
        method="POST",
        url=CALLBACK_URL_V2,
        payload=ds_08p_callback_payload,
    )

    with pytest.raises(ValueError, match="Unsupported signature digest algorithm 'SHA1'"):
        sign_srtp_message(
            method="POST",
            url=CALLBACK_URL_V2,
            headers=SIGNING_HEADERS,
            body=body,
            key_material=qsealc_key_material,
            algorithm="SHA1",
        )


@allure.epic("QSealC message signing")
@allure.feature("Signature generation")
@allure.story("Encode certificate material for transport")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_sign_srtp_message_encodes_leaf_der_and_chain_pem(
    qsealc_key_material,
    ds_08p_callback_payload,
    callback_body_factory,
) -> None:
    """Encode the leaf certificate as DER and the chain as PEM."""
    body = callback_body_factory(
        method="POST",
        url=CALLBACK_URL_V2,
        payload=ds_08p_callback_payload,
    )
    signed_message = sign_srtp_message(
        method="POST",
        url=CALLBACK_URL_V2,
        headers=SIGNING_HEADERS,
        body=body,
        key_material=qsealc_key_material,
    )

    leaf_certificate = x509.load_der_x509_certificate(base64.b64decode(signed_message.certificate_base64))
    expected_certificate = x509.load_pem_x509_certificate(qsealc_key_material.certificate_pem)

    assert leaf_certificate.public_bytes(Encoding.DER) == expected_certificate.public_bytes(Encoding.DER), (
        "Expected the certificate header to contain the leaf certificate in DER form"
    )
    assert base64.b64decode(signed_message.certificate_chain_base64) == qsealc_key_material.certificate_pem, (
        "Expected the chain header to contain the PEM certificate fallback"
    )
