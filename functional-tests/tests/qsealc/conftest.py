"""Fixtures and generated certificate material for QSealC tests."""

from datetime import datetime, timedelta, timezone

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import NameOID

from utils.cryptography_utils import QsealcKeyMaterial
from utils.dataset_callback_data_DS_08P_positive_v2 import generate_callback_data_DS_08P_positive_compliant
from utils.qsealc_test_certificates import (
    QsealcTestChain,
    TEST_CERTIFICATE_LIFETIME,
    TEST_RSA_KEY_SIZE,
    TEST_RSA_PUBLIC_EXPONENT,
    generate_qsealc_test_chain,
)
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
    """Create an ephemeral RSA root and leaf certificate chain for signature tests."""
    return generate_qsealc_test_chain()


@pytest.fixture
def ds_08p_callback_payload() -> JsonType:
    """Return a valid DS-08P callback payload for signing scenarios."""
    return generate_callback_data_DS_08P_positive_compliant()
