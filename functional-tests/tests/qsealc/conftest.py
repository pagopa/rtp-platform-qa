"""Fixtures and generated certificate material for QSealC tests."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import NameOID

from utils.cryptography_utils import QsealcKeyMaterial
from utils.dataset_callback_data_DS_08P_positive_v2 import generate_callback_data_DS_08P_positive_compliant
from utils.type_utils import JsonType

TEST_RSA_PUBLIC_EXPONENT = 65537
TEST_RSA_KEY_SIZE = 2048
TEST_CERTIFICATE_LIFETIME = timedelta(days=1)


@dataclass(frozen=True)
class QsealcTestChain:
    key_material: QsealcKeyMaterial
    root_certificate_pem: bytes


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
    root_private_key = rsa.generate_private_key(
        public_exponent=TEST_RSA_PUBLIC_EXPONENT,
        key_size=TEST_RSA_KEY_SIZE,
    )
    leaf_private_key = rsa.generate_private_key(
        public_exponent=TEST_RSA_PUBLIC_EXPONENT,
        key_size=TEST_RSA_KEY_SIZE,
    )
    root_subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test QTSP Root")])
    leaf_subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test QSealC Signer")])
    valid_from = datetime.now(timezone.utc) - timedelta(minutes=1)
    valid_until = valid_from + TEST_CERTIFICATE_LIFETIME
    root_certificate = (
        x509.CertificateBuilder()
        .subject_name(root_subject)
        .issuer_name(root_subject)
        .public_key(root_private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(valid_from)
        .not_valid_after(valid_until)
        .add_extension(x509.BasicConstraints(ca=True, path_length=1), critical=True)
        .sign(private_key=root_private_key, algorithm=hashes.SHA256())
    )
    leaf_certificate = (
        x509.CertificateBuilder()
        .subject_name(leaf_subject)
        .issuer_name(root_subject)
        .public_key(leaf_private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(valid_from)
        .not_valid_after(valid_until)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(private_key=root_private_key, algorithm=hashes.SHA256())
    )
    root_certificate_pem = root_certificate.public_bytes(Encoding.PEM)

    return QsealcTestChain(
        key_material=QsealcKeyMaterial(
            private_key=leaf_private_key,
            certificate_pem=leaf_certificate.public_bytes(Encoding.PEM),
            certificate_chain_pem=root_certificate_pem,
        ),
        root_certificate_pem=root_certificate_pem,
    )


@pytest.fixture
def ds_08p_callback_payload() -> JsonType:
    """Return a valid DS-08P callback payload for signing scenarios."""
    return generate_callback_data_DS_08P_positive_compliant()
