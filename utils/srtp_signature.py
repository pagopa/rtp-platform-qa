"""Generate EPC SRTP QSealC signatures and transport headers."""

import base64
import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.serialization import Encoding

from utils.cryptography_utils import QsealcKeyMaterial
from utils.srtp_message_signing import build_canonical_representation

SRTP_SIGNATURE_HEADER: Final = "X-SRTP-Signature"
SRTP_SIGNATURE_CERTIFICATE_HEADER: Final = "X-SRTP-Signature-Certificate"
SRTP_CERTIFICATE_CHAIN_HEADER: Final = "X-SRTP-Signature-Certificate-Chain"
SRTP_SIGNATURE_ALGORITHM_DIGEST_HEADER: Final = "X-SRTP-Signature-Algorithm-Digest"
DEFAULT_SIGNATURE_ALGORITHM: Final = "sha256"
ALLOWED_SIGNATURE_DIGEST_ALGORITHMS: Final = frozenset(
    {
        "sha256",
        "sha384",
        "sha512",
        "sha3-256",
        "sha3-384",
        "sha3-512",
    }
)


@dataclass(frozen=True)
class SrtpSignature:
    """Detached SRTP signature and its transport values."""

    signature_base64: str
    certificate_base64: str
    certificate_chain_base64: str
    digest_base64: str
    algorithm: str

    def as_headers(self) -> dict[str, str]:
        """Return the HTTP headers required to transport this signature."""
        return {
            SRTP_SIGNATURE_HEADER: self.signature_base64,
            SRTP_SIGNATURE_CERTIFICATE_HEADER: self.certificate_base64,
            SRTP_CERTIFICATE_CHAIN_HEADER: self.certificate_chain_base64,
            SRTP_SIGNATURE_ALGORITHM_DIGEST_HEADER: self.algorithm,
        }


def sign_srtp_message(
    *,
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: bytes,
    key_material: QsealcKeyMaterial,
    algorithm: str = DEFAULT_SIGNATURE_ALGORITHM,
) -> SrtpSignature:
    """Sign the exact SRTP message bytes and build its signature headers."""
    normalized_algorithm = _normalize_algorithm(algorithm)
    hash_algorithm = _hash_algorithm(normalized_algorithm)
    canonical_bytes = build_canonical_representation(
        method=method,
        url=url,
        headers=headers,
        body=body,
    )
    signature = _sign(canonical_bytes, key_material.private_key, hash_algorithm)
    certificate = x509.load_pem_x509_certificate(key_material.certificate_pem)
    chain_bytes = key_material.certificate_chain_pem or key_material.certificate_pem

    return SrtpSignature(
        signature_base64=_encode_base64(signature),
        certificate_base64=_encode_base64(certificate.public_bytes(Encoding.DER)),
        certificate_chain_base64=_encode_base64(chain_bytes),
        digest_base64=_encode_base64(hashlib.new(normalized_algorithm, canonical_bytes).digest()),
        algorithm=normalized_algorithm,
    )


def _normalize_algorithm(algorithm: str) -> str:
    normalized_algorithm = algorithm.lower().replace("_", "-")
    if normalized_algorithm not in ALLOWED_SIGNATURE_DIGEST_ALGORITHMS:
        allowed_algorithms = ", ".join(sorted(ALLOWED_SIGNATURE_DIGEST_ALGORITHMS))
        raise ValueError(
            f"Unsupported signature digest algorithm '{algorithm}'; allowed: {allowed_algorithms}."
        )
    return normalized_algorithm


def _hash_algorithm(algorithm: str) -> hashes.HashAlgorithm:
    hash_algorithms = {
        "sha256": hashes.SHA256,
        "sha384": hashes.SHA384,
        "sha512": hashes.SHA512,
        "sha3-256": hashes.SHA3_256,
        "sha3-384": hashes.SHA3_384,
        "sha3-512": hashes.SHA3_512,
        "sha3-256": hashes.SHA3_256,
        "sha3-384": hashes.SHA3_384,
        "sha3-512": hashes.SHA3_512,
    }
    return hash_algorithms[algorithm]()


def _sign(
    canonical_bytes: bytes,
    private_key: RSAPrivateKey | EllipticCurvePrivateKey,
    hash_algorithm: hashes.HashAlgorithm,
) -> bytes:
    if isinstance(private_key, RSAPrivateKey):
        return private_key.sign(
            data=canonical_bytes,
            padding=padding.PKCS1v15(),
            algorithm=hash_algorithm,
        )
    if isinstance(private_key, EllipticCurvePrivateKey):
        return private_key.sign(
            data=canonical_bytes,
            signature_algorithm=ec.ECDSA(hash_algorithm),
        )
    raise TypeError("QSealC private key must be RSA or elliptic curve")


def _encode_base64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")
