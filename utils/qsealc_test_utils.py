"""Shared test types for QSealC certificate fixtures."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

from api.utils.endpoints import CALLBACK_URL_V2
from api.utils.http_utils import APPLICATION_JSON_HEADER
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import NameOID
from utils.cryptography_utils import QsealcKeyMaterial
from utils.srtp_signature import sign_srtp_message

TEST_RSA_PUBLIC_EXPONENT = 65537
TEST_RSA_KEY_SIZE = 2048
TEST_CERTIFICATE_LIFETIME = timedelta(days=1)


@dataclass(frozen=True)
class QsealcTestChain:
    """Hold the generated QSealC chain and its validity metadata."""

    key_material: QsealcKeyMaterial
    root_certificate_pem: bytes
    valid_until: datetime


@dataclass(frozen=True)
class QsealcVerificationContext:
    """Hold the signed message inputs shared by verification scenarios."""

    body: bytes
    headers: Mapping[str, str]
    trusted_roots: tuple[bytes, ...]


def create_qsealc_test_chain(
    *,
    missing_root_extension: Literal["basic_constraints", "key_usage"] | None = None,
) -> QsealcTestChain:
    """Create a generated QSealC chain with optionally incomplete root constraints."""
    root_private_key = rsa.generate_private_key(
        public_exponent=TEST_RSA_PUBLIC_EXPONENT,
        key_size=TEST_RSA_KEY_SIZE,
    )
    leaf_private_key = rsa.generate_private_key(
        public_exponent=TEST_RSA_PUBLIC_EXPONENT,
        key_size=TEST_RSA_KEY_SIZE,
    )
    root_subject = x509.Name(
        [x509.NameAttribute(oid=NameOID.COMMON_NAME, value="Test QTSP Root")]
    )
    leaf_subject = x509.Name(
        [x509.NameAttribute(oid=NameOID.COMMON_NAME, value="Test QSealC Signer")]
    )
    valid_from = datetime.now(timezone.utc) - timedelta(minutes=1)
    valid_until = valid_from + TEST_CERTIFICATE_LIFETIME
    root_builder = (
        x509.CertificateBuilder()
        .subject_name(root_subject)
        .issuer_name(root_subject)
        .public_key(root_private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(valid_from)
        .not_valid_after(valid_until)
    )
    if missing_root_extension != "basic_constraints":
        root_builder = root_builder.add_extension(
            x509.BasicConstraints(ca=True, path_length=1),
            critical=True,
        )
    if missing_root_extension != "key_usage":
        root_builder = root_builder.add_extension(
            x509.KeyUsage(
                digital_signature=False,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
    root_certificate = root_builder.sign(
        private_key=root_private_key,
        algorithm=hashes.SHA256(),
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
        valid_until=valid_until,
    )


def build_qsealc_verification_context(
    *,
    key_material: QsealcKeyMaterial,
    root_certificate_pem: bytes,
    body: bytes,
) -> QsealcVerificationContext:
    """Create a signed callback verification context from generated key material."""
    signature = sign_srtp_message(
        method="POST",
        url=CALLBACK_URL_V2,
        headers=APPLICATION_JSON_HEADER,
        body=body,
        key_material=key_material,
    )
    return QsealcVerificationContext(
        body=body,
        headers={**APPLICATION_JSON_HEADER, **signature.as_headers()},
        trusted_roots=(root_certificate_pem,),
    )
