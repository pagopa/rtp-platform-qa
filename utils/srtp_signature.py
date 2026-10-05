"""Generate EPC SRTP QSealC signatures and transport headers."""

import base64
import binascii
import hashlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Final

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
from cryptography.hazmat.primitives.asymmetric.padding import AsymmetricPadding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509 import Certificate
from cryptography.x509.extensions import ExtensionNotFound

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


TrustedRoot = bytes | str | Certificate


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


@dataclass(frozen=True)
class SrtpVerificationResult:
    """Outcome of SRTP signature and certificate validation."""

    is_valid: bool
    failure_reason: str | None = None
    failure_detail: str | None = None
    validated_certificate_chain_length: int = 0


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
    normalized_algorithm = normalize_signature_algorithm(algorithm)
    hash_algorithm = signature_hash_algorithm(normalized_algorithm)
    canonical_bytes = build_canonical_representation(
        method=method,
        url=url,
        headers=headers,
        body=body,
    )
    signature = _sign(
        canonical_bytes=canonical_bytes,
        private_key=key_material.private_key,
        hash_algorithm=hash_algorithm,
    )
    certificate = x509.load_pem_x509_certificate(key_material.certificate_pem)
    chain_bytes = key_material.certificate_chain_pem or key_material.certificate_pem

    return SrtpSignature(
        signature_base64=_encode_base64(signature),
        certificate_base64=_encode_base64(certificate.public_bytes(Encoding.DER)),
        certificate_chain_base64=_encode_base64(chain_bytes),
        digest_base64=_encode_base64(hashlib.new(normalized_algorithm, canonical_bytes).digest()),
        algorithm=normalized_algorithm,
    )


def verify_srtp_message(
    *,
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: bytes,
    trusted_roots: Iterable[TrustedRoot] | TrustedRoot,
) -> SrtpVerificationResult:
    """Verify an SRTP signature against a trusted certificate chain."""
    signature_value = _header_value(headers=headers, name=SRTP_SIGNATURE_HEADER)
    certificate_value = _header_value(headers=headers, name=SRTP_SIGNATURE_CERTIFICATE_HEADER)
    chain_value = _header_value(headers=headers, name=SRTP_CERTIFICATE_CHAIN_HEADER)
    if not signature_value or not certificate_value or not chain_value:
        return _verification_failure(
            reason="MISSING_MANDATORY_HEADERS",
            detail="Signature, signer certificate, and certificate chain headers are required",
        )

    try:
        signature = base64.b64decode(signature_value, validate=True)
        signer_certificates = _decode_certificates(base64.b64decode(certificate_value, validate=True))
        chain_certificates = _decode_certificates(base64.b64decode(chain_value, validate=True))
        root_certificates = _load_trusted_roots(trusted_roots)
    except (binascii.Error, ValueError) as error:
        return _verification_failure(
            reason="MALFORMED_CERTIFICATE",
            detail=f"Invalid signature or certificate encoding: {error}",
        )

    if not signer_certificates:
        return _verification_failure(
            reason="MALFORMED_CERTIFICATE",
            detail="The signer certificate header did not contain a certificate",
        )
    if not root_certificates:
        return _verification_failure(
            reason="TRUST_STORE_EMPTY",
            detail="At least one trusted root certificate is required",
        )

    leaf_certificate = signer_certificates[0]
    validated_chain = _build_certificate_chain(
        leaf_certificate=leaf_certificate,
        candidate_certificates=(*signer_certificates[1:], *chain_certificates),
        trusted_roots=root_certificates,
    )
    if validated_chain is None:
        return _verification_failure(
            reason="UNTRUSTED_ISSUER",
            detail="The signer certificate chain does not terminate at a trusted root",
        )

    algorithm_value = (
        _header_value(headers=headers, name=SRTP_SIGNATURE_ALGORITHM_DIGEST_HEADER) or DEFAULT_SIGNATURE_ALGORITHM
    )
    try:
        normalized_algorithm = normalize_signature_algorithm(algorithm_value)
        hash_algorithm = signature_hash_algorithm(normalized_algorithm)
    except ValueError as error:
        return _verification_failure(
            reason="INVALID_SIGNATURE",
            detail=str(error),
            chain_length=len(validated_chain),
        )

    canonical_bytes = build_canonical_representation(
        method=method,
        url=url,
        headers=headers,
        body=body,
    )
    if not _verify_signature(
        certificate=leaf_certificate,
        signature=signature,
        canonical_bytes=canonical_bytes,
        hash_algorithm=hash_algorithm,
    ):
        return _verification_failure(
            reason="INVALID_SIGNATURE",
            detail="The signature does not match the canonical message",
            chain_length=len(validated_chain),
        )

    return SrtpVerificationResult(
        is_valid=True,
        validated_certificate_chain_length=len(validated_chain),
    )


def normalize_signature_algorithm(algorithm: str) -> str:
    normalized_algorithm = algorithm.lower().replace("_", "-")
    if normalized_algorithm not in ALLOWED_SIGNATURE_DIGEST_ALGORITHMS:
        allowed_algorithms = ", ".join(sorted(ALLOWED_SIGNATURE_DIGEST_ALGORITHMS))
        raise ValueError(
            f"Unsupported signature digest algorithm '{algorithm}'; allowed: {allowed_algorithms}."
        )
    return normalized_algorithm


def signature_hash_algorithm(algorithm: str) -> hashes.HashAlgorithm:
    hash_algorithms = {
        "sha256": hashes.SHA256,
        "sha384": hashes.SHA384,
        "sha512": hashes.SHA512,
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
    """Sign canonical message bytes with an RSA or elliptic curve private key."""
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
    """Encode bytes as an ASCII Base64 string."""
    return base64.b64encode(value).decode("ascii")


def _header_value(headers: Mapping[str, str], name: str) -> str | None:
    return next((value for header_name, value in headers.items() if header_name.lower() == name.lower()), None)


def _decode_certificates(value: bytes) -> tuple[Certificate, ...]:
    if not value:
        raise ValueError("Certificate value is empty")
    if b"-----BEGIN CERTIFICATE-----" in value:
        return tuple(x509.load_pem_x509_certificates(value))
    return (x509.load_der_x509_certificate(value),)


def _load_trusted_roots(trusted_roots: Iterable[TrustedRoot] | TrustedRoot) -> tuple[Certificate, ...]:
    if isinstance(trusted_roots, (bytes, str, Certificate)):
        roots = (trusted_roots,)
    else:
        roots = tuple(trusted_roots)

    certificates: list[Certificate] = []
    for root in roots:
        if isinstance(root, Certificate):
            certificates.append(root)
            continue
        root_bytes = root.encode() if isinstance(root, str) else root
        certificates.extend(_decode_certificates(root_bytes))
    return tuple(certificates)


def _build_certificate_chain(
    *,
    leaf_certificate: Certificate,
    candidate_certificates: Iterable[Certificate],
    trusted_roots: Iterable[Certificate],
    max_depth: int = 10,
) -> tuple[Certificate, ...] | None:
    trusted_by_fingerprint = {
        certificate.fingerprint(hashes.SHA256()): certificate for certificate in trusted_roots
    }
    chain = [leaf_certificate]
    candidates = _deduplicate_certificates((*candidate_certificates, *trusted_by_fingerprint.values()))
    current = leaf_certificate

    if _certificate_fingerprint(current) in trusted_by_fingerprint:
        return tuple(chain)

    for _ in range(max_depth):
        issuer = next(
            (
                candidate
                for candidate in candidates
                if _certificate_fingerprint(candidate) not in {_certificate_fingerprint(item) for item in chain}
                and candidate.subject == current.issuer
                and _is_ca_certificate(candidate)
                and _verify_certificate_signature(certificate=current, issuer=candidate)
            ),
            None,
        )
        if issuer is None:
            return None
        chain.append(issuer)
        if _certificate_fingerprint(issuer) in trusted_by_fingerprint:
            return tuple(chain)
        current = issuer

    return None


def _deduplicate_certificates(certificates: Iterable[Certificate]) -> tuple[Certificate, ...]:
    unique_certificates: dict[bytes, Certificate] = {}
    for certificate in certificates:
        unique_certificates.setdefault(_certificate_fingerprint(certificate), certificate)
    return tuple(unique_certificates.values())


def _certificate_fingerprint(certificate: Certificate) -> bytes:
    return certificate.fingerprint(hashes.SHA256())


def _is_ca_certificate(certificate: Certificate) -> bool:
    try:
        return certificate.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
    except ExtensionNotFound:
        return True


def _verify_certificate_signature(certificate: Certificate, issuer: Certificate) -> bool:
    issuer_public_key = issuer.public_key()
    try:
        if isinstance(issuer_public_key, RSAPublicKey):
            issuer_public_key.verify(
                signature=certificate.signature,
                data=certificate.tbs_certificate_bytes,
                padding=padding.PKCS1v15(),
                algorithm=certificate.signature_hash_algorithm,
            )
        elif isinstance(issuer_public_key, ec.EllipticCurvePublicKey):
            issuer_public_key.verify(
                signature=certificate.signature,
                data=certificate.tbs_certificate_bytes,
                signature_algorithm=ec.ECDSA(certificate.signature_hash_algorithm),
            )
        else:
            return False
    except (InvalidSignature, ValueError):
        return False
    return True


def _verify_signature(
    *,
    certificate: Certificate,
    signature: bytes,
    canonical_bytes: bytes,
    hash_algorithm: hashes.HashAlgorithm,
) -> bool:
    public_key = certificate.public_key()
    if isinstance(public_key, RSAPublicKey):
        return _verify_rsa_signature(
            public_key=public_key,
            signature=signature,
            canonical_bytes=canonical_bytes,
            hash_algorithm=hash_algorithm,
        )
    if isinstance(public_key, ec.EllipticCurvePublicKey):
        return _verify_elliptic_curve_signature(
            public_key=public_key,
            signature=signature,
            canonical_bytes=canonical_bytes,
            hash_algorithm=hash_algorithm,
        )
    return False


def _verify_rsa_signature(
    *,
    public_key: RSAPublicKey,
    signature: bytes,
    canonical_bytes: bytes,
    hash_algorithm: hashes.HashAlgorithm,
) -> bool:
    return any(
        _verify_rsa_signature_with_padding(
            public_key=public_key,
            signature=signature,
            canonical_bytes=canonical_bytes,
            hash_algorithm=hash_algorithm,
            signature_padding=signature_padding,
        )
        for signature_padding in (
            padding.PKCS1v15(),
            padding.PSS(mgf=padding.MGF1(hash_algorithm), salt_length=padding.PSS.DIGEST_LENGTH),
        )
    )


def _verify_rsa_signature_with_padding(
    *,
    public_key: RSAPublicKey,
    signature: bytes,
    canonical_bytes: bytes,
    hash_algorithm: hashes.HashAlgorithm,
    signature_padding: AsymmetricPadding,
) -> bool:
    try:
        public_key.verify(
            signature=signature,
            data=canonical_bytes,
            padding=signature_padding,
            algorithm=hash_algorithm,
        )
    except InvalidSignature:
        return False
    return True


def _verify_elliptic_curve_signature(
    *,
    public_key: ec.EllipticCurvePublicKey,
    signature: bytes,
    canonical_bytes: bytes,
    hash_algorithm: hashes.HashAlgorithm,
) -> bool:
    try:
        public_key.verify(
            signature=signature,
            data=canonical_bytes,
            signature_algorithm=ec.ECDSA(hash_algorithm),
        )
    except InvalidSignature:
        return False
    return True


def _verification_failure(
    *,
    reason: str,
    detail: str,
    chain_length: int = 0,
) -> SrtpVerificationResult:
    return SrtpVerificationResult(
        is_valid=False,
        failure_reason=reason,
        failure_detail=detail,
        validated_certificate_chain_length=chain_length,
    )
