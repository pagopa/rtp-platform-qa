"""Fixtures and generated certificate material for QSealC tests."""

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import NameOID

from api.utils.endpoints import CALLBACK_URL_V2
from api.utils.http_utils import APPLICATION_JSON_HEADER
from utils.cryptography_utils import QsealcKeyMaterial
from utils.dataset_callback_data_DS_08P_positive_v2 import generate_callback_data_DS_08P_positive_compliant
from utils.qsealc_test_utils import (
    TEST_CERTIFICATE_LIFETIME,
    TEST_RSA_KEY_SIZE,
    TEST_RSA_PUBLIC_EXPONENT,
    QsealcTestChain,
    QsealcVerificationContext,
    build_qsealc_verification_context,
    create_qsealc_test_chain,
)
from utils.srtp_message_signing import serialize_json_request_body
from utils.type_utils import JsonType


@pytest.fixture
def qsealc_key_material() -> QsealcKeyMaterial:
    """Create an ephemeral self-signed RSA key pair for signature tests."""
    private_key = rsa.generate_private_key(
        public_exponent=TEST_RSA_PUBLIC_EXPONENT,
        key_size=TEST_RSA_KEY_SIZE,
    )
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test QSealC Signer")])
    valid_from = datetime.now(timezone.utc) - timedelta(minutes=1)
    valid_until = valid_from + TEST_CERTIFICATE_LIFETIME
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(valid_from)
        .not_valid_after(valid_until)
        .sign(private_key=private_key, algorithm=hashes.SHA256())
    )

    return QsealcKeyMaterial(
        private_key=private_key,
        certificate_pem=certificate.public_bytes(Encoding.PEM),
        certificate_chain_pem=b"",
    )


@pytest.fixture
def qsealc_test_chain() -> QsealcTestChain:
    return create_qsealc_test_chain()


@pytest.fixture
def callback_body_factory() -> Callable[..., bytes]:
    """Return a factory that serializes callback payloads like Requests does."""
    return serialize_json_request_body


@pytest.fixture
def ds_08p_callback_payload() -> JsonType:
    """Return a valid DS-08P callback payload for signing scenarios."""
    return generate_callback_data_DS_08P_positive_compliant()


@pytest.fixture
def callback_body(ds_08p_callback_payload, callback_body_factory) -> bytes:
    """Return the prepared body for the standard v2 callback."""
    return callback_body_factory(
        method="POST",
        url=CALLBACK_URL_V2,
        payload=ds_08p_callback_payload,
    )


@pytest.fixture
def qsealc_verification_context(
    qsealc_test_chain: QsealcTestChain,
    callback_body: bytes,
) -> QsealcVerificationContext:
    return build_qsealc_verification_context(
        key_material=qsealc_test_chain.key_material,
        root_certificate_pem=qsealc_test_chain.root_certificate_pem,
        body=callback_body,
    )


@pytest.fixture(
    params=("basic_constraints", "key_usage"),
    ids=("missing-basic-constraints", "missing-key-usage"),
)
def qsealc_verification_context_without_ca_constraints(
    request,
    callback_body: bytes,
) -> QsealcVerificationContext:
    chain = create_qsealc_test_chain(missing_root_extension=request.param)
    return build_qsealc_verification_context(
        key_material=chain.key_material,
        root_certificate_pem=chain.root_certificate_pem,
        body=callback_body,
    )
