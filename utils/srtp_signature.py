"""Generate EPC SRTP QSealC signatures and transport headers."""

import base64
import binascii
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Final

from cryptography import x509
from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
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


class RevocationStatus(StrEnum):
    """Status returned by a CRL or OCSP revocation adapter."""

    GOOD = "GOOD"
    REVOKED = "REVOKED"
    UNKNOWN = "UNKNOWN"
    SKIPPED = "SKIPPED"


@dataclass(frozen=True)
class RevocationResult:
    """Outcome of a single certificate revocation check."""

    status: RevocationStatus
    source: str
    reason: str | None = None


RevocationChecker = Callable[[Certificate, Certificate], RevocationResult]
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
    revocation_status: RevocationStatus = RevocationStatus.SKIPPED
    validated_certificate_chain_length: int = 0


@dataclass(frozen=True)
class _DecodedVerificationMaterial:
    """Decoded signature values and certificates needed for validation."""

    signature: bytes
    leaf_certificate: Certificate
    candidate_certificates: tuple[Certificate, ...]
    trusted_roots: tuple[Certificate, ...]


@dataclass(frozen=True)
class _ValidatedVerificationContext:
    """Validated certificate context used to verify the canonical message."""

    signature: bytes
    leaf_certificate: Certificate
    validated_chain: tuple[Certificate, ...]
    revocation_status: RevocationStatus


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
    digest = hashes.Hash(hash_algorithm)
    digest.update(canonical_bytes)
    certificate = x509.load_pem_x509_certificate(key_material.certificate_pem)
    chain_bytes = key_material.certificate_chain_pem or key_material.certificate_pem

    return SrtpSignature(
        signature_base64=_encode_base64(signature),
        certificate_base64=_encode_base64(certificate.public_bytes(Encoding.DER)),
        certificate_chain_base64=_encode_base64(chain_bytes),
        digest_base64=_encode_base64(digest.finalize()),
        algorithm=normalized_algorithm,
    )


def verify_srtp_message(
    *,
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: bytes,
    trusted_roots: Iterable[TrustedRoot] | TrustedRoot,
    at_time: datetime | None = None,
    clock_skew_seconds: int = 60,
    revocation_checker: RevocationChecker | None = None,
) -> SrtpVerificationResult:
    """Verify an SRTP signature, certificate chain, validity, and revocation status."""
    decoded_material = _decode_verification_material(
        headers=headers,
        trusted_roots=trusted_roots,
    )

    decoded_material_is_failure = isinstance(decoded_material, SrtpVerificationResult)
    if decoded_material_is_failure:
        return decoded_material

    validated_context = _validate_verification_context(
        decoded_material=decoded_material,
        at_time=at_time,
        clock_skew_seconds=clock_skew_seconds,
        revocation_checker=revocation_checker,
    )

    validated_context_is_failure = isinstance(validated_context, SrtpVerificationResult)
    if validated_context_is_failure:
        return validated_context

    verification_failure = _verify_canonical_message(
        method=method,
        url=url,
        headers=headers,
        body=body,
        context=validated_context,
    )

    if verification_failure is not None:
        return verification_failure

    return SrtpVerificationResult(
        is_valid=True,
        revocation_status=validated_context.revocation_status,
        validated_certificate_chain_length=len(validated_context.validated_chain),
    )


def _decode_verification_material(
    *,
    headers: Mapping[str, str],
    trusted_roots: Iterable[TrustedRoot] | TrustedRoot,
) -> _DecodedVerificationMaterial | SrtpVerificationResult:
    """Decode signature headers and trusted certificates."""
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

    return _DecodedVerificationMaterial(
        signature=signature,
        leaf_certificate=signer_certificates[0],
        candidate_certificates=(*signer_certificates[1:], *chain_certificates),
        trusted_roots=root_certificates,
    )


def _validate_verification_context(
    *,
    decoded_material: _DecodedVerificationMaterial,
    at_time: datetime | None,
    clock_skew_seconds: int,
    revocation_checker: RevocationChecker | None,
) -> _ValidatedVerificationContext | SrtpVerificationResult:
    """Validate the certificate path and apply the revocation adapter."""
    validated_chain = _validate_certificate_path(
        leaf_certificate=decoded_material.leaf_certificate,
        candidate_certificates=decoded_material.candidate_certificates,
        trusted_roots=decoded_material.trusted_roots,
        at_time=at_time,
        clock_skew_seconds=clock_skew_seconds,
    )

    validated_chain_is_failure = isinstance(validated_chain, SrtpVerificationResult)
    if validated_chain_is_failure:
        return validated_chain

    revocation_status, revocation_failure = _validate_revocation(
        certificates=validated_chain,
        revocation_checker=revocation_checker,
    )

    if revocation_failure is not None:
        return _verification_failure(
            reason="CERTIFICATE_REVOKED",
            detail=revocation_failure,
            revocation_status=revocation_status,
            chain_length=len(validated_chain),
        )

    return _ValidatedVerificationContext(
        signature=decoded_material.signature,
        leaf_certificate=decoded_material.leaf_certificate,
        validated_chain=validated_chain,
        revocation_status=revocation_status,
    )


def _validate_certificate_path(
    *,
    leaf_certificate: Certificate,
    candidate_certificates: Iterable[Certificate],
    trusted_roots: Iterable[Certificate],
    at_time: datetime | None,
    clock_skew_seconds: int,
) -> tuple[Certificate, ...] | SrtpVerificationResult:
    """Build and validate the signer certificate path."""
    validated_chain = _build_certificate_chain(
        leaf_certificate=leaf_certificate,
        candidate_certificates=candidate_certificates,
        trusted_roots=trusted_roots,
    )

    if validated_chain is None:
        return _verification_failure(
            reason="UNTRUSTED_ISSUER",
            detail="The signer certificate chain does not terminate at a trusted root",
        )

    chain_constraints_are_valid = _validate_certificate_chain_constraints(validated_chain)
    if not chain_constraints_are_valid:
        return _verification_failure(
            reason="INVALID_CERTIFICATE_CHAIN",
            detail="The signer certificate chain violates CA constraints",
            chain_length=len(validated_chain),
        )

    verification_time = _as_utc(at_time or datetime.now(timezone.utc))
    validity_failure = _validate_certificate_validity(
        certificates=validated_chain,
        at_time=verification_time,
        clock_skew_seconds=clock_skew_seconds,
    )

    if validity_failure is not None:
        return _verification_failure(
            reason=validity_failure,
            detail=f"A certificate in the signer chain failed {validity_failure.lower()} validation",
            chain_length=len(validated_chain),
        )

    leaf_certificate_is_valid = _is_valid_leaf_certificate(leaf_certificate)
    if not leaf_certificate_is_valid:
        return _verification_failure(
            reason="INVALID_CERTIFICATE_PROFILE",
            detail="The signer certificate is not a valid end-entity signing certificate",
            chain_length=len(validated_chain),
        )

    return validated_chain


def _verify_canonical_message(
    *,
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: bytes,
    context: _ValidatedVerificationContext,
) -> SrtpVerificationResult | None:
    """Verify the detached signature against the canonical request bytes."""
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
            revocation_status=context.revocation_status,
            chain_length=len(context.validated_chain),
        )

    try:
        canonical_bytes = build_canonical_representation(
            method=method,
            url=url,
            headers=headers,
            body=body,
        )
    except ValueError as error:
        return _verification_failure(
            reason="INVALID_MESSAGE",
            detail=str(error),
            revocation_status=context.revocation_status,
            chain_length=len(context.validated_chain),
        )

    signature_is_valid = _verify_signature(
        certificate=context.leaf_certificate,
        signature=context.signature,
        canonical_bytes=canonical_bytes,
        hash_algorithm=hash_algorithm,
    )

    if not signature_is_valid:
        return _verification_failure(
            reason="INVALID_SIGNATURE",
            detail="The signature does not match the canonical message",
            revocation_status=context.revocation_status,
            chain_length=len(context.validated_chain),
        )

    return None


def normalize_signature_algorithm(algorithm: str) -> str:
    """Normalize and validate a supported signature digest algorithm name."""
    normalized_algorithm = algorithm.lower().replace("_", "-")
    if normalized_algorithm not in ALLOWED_SIGNATURE_DIGEST_ALGORITHMS:
        allowed_algorithms = ", ".join(sorted(ALLOWED_SIGNATURE_DIGEST_ALGORITHMS))
        raise ValueError(
            f"Unsupported signature digest algorithm '{algorithm}'; allowed: {allowed_algorithms}."
        )
    return normalized_algorithm


def signature_hash_algorithm(algorithm: str) -> hashes.HashAlgorithm:
    """Return the cryptography hash implementation for a normalized algorithm."""
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
    """Sign canonical message bytes with the supported QSealC key type."""
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
    """Encode binary transport data as ASCII Base64."""
    return base64.b64encode(value).decode("ascii")


def _header_value(headers: Mapping[str, str], name: str) -> str | None:
    """Return a header value using case-insensitive header-name matching."""
    return next((value for header_name, value in headers.items() if header_name.lower() == name.lower()), None)


def _decode_certificates(value: bytes) -> tuple[Certificate, ...]:
    """Decode a DER certificate or one or more concatenated PEM certificates."""
    if not value:
        raise ValueError("Certificate value is empty")
    if b"-----BEGIN CERTIFICATE-----" in value:
        return tuple(x509.load_pem_x509_certificates(value))
    return (x509.load_der_x509_certificate(value),)


def _load_trusted_roots(trusted_roots: Iterable[TrustedRoot] | TrustedRoot) -> tuple[Certificate, ...]:
    """Load trusted-root certificates from certificate objects or encoded bytes."""
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
    """Build and cryptographically validate a leaf-to-trusted-root certificate chain."""
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
    """Remove duplicate certificates while preserving their first-seen order."""
    unique_certificates: dict[bytes, Certificate] = {}
    for certificate in certificates:
        unique_certificates.setdefault(_certificate_fingerprint(certificate), certificate)
    return tuple(unique_certificates.values())


def _certificate_fingerprint(certificate: Certificate) -> bytes:
    """Return the SHA-256 fingerprint used to identify a certificate."""
    return certificate.fingerprint(hashes.SHA256())


def _is_ca_certificate(certificate: Certificate) -> bool:
    """Return whether a certificate may act as a certificate authority."""
    ca_constraints = _certificate_ca_constraints(certificate)
    return (
        ca_constraints is not None
        and ca_constraints[0].ca
        and ca_constraints[1].key_cert_sign
    )


def _verify_certificate_signature(certificate: Certificate, issuer: Certificate) -> bool:
    """Verify that an issuer certificate signed the candidate certificate."""
    try:
        return _verify_with_public_key(
            public_key=issuer.public_key(),
            signature=certificate.signature,
            data=certificate.tbs_certificate_bytes,
            hash_algorithm=certificate.signature_hash_algorithm,
            rsa_paddings=(padding.PKCS1v15(),),
        )
    except (UnsupportedAlgorithm, ValueError):
        return False


def _validate_certificate_validity(
    *,
    certificates: Iterable[Certificate],
    at_time: datetime,
    clock_skew_seconds: int,
) -> str | None:
    """Return a validity failure for the chain, accounting for clock skew."""
    at_timestamp = at_time.timestamp()
    for certificate in certificates:
        not_before = _certificate_datetime(certificate=certificate, attribute="not_valid_before")
        not_after = _certificate_datetime(certificate=certificate, attribute="not_valid_after")
        if at_timestamp + clock_skew_seconds < not_before.timestamp():
            return "CERTIFICATE_NOT_YET_VALID"
        if at_timestamp - clock_skew_seconds > not_after.timestamp():
            return "CERTIFICATE_EXPIRED"
    return None


def _validate_certificate_chain_constraints(certificates: tuple[Certificate, ...]) -> bool:
    """Validate CA, key-usage, and path-length constraints on a certificate chain."""
    for index, certificate in enumerate(certificates[1:], start=1):
        ca_constraints = _certificate_ca_constraints(certificate)
        if ca_constraints is None:
            return False
        basic_constraints, key_usage = ca_constraints
        if not basic_constraints.ca or not key_usage.key_cert_sign:
            return False
        if basic_constraints.path_length is not None:
            subordinate_ca_count = sum(
                _is_ca_certificate(subordinate) for subordinate in certificates[1:index]
            )
            if subordinate_ca_count > basic_constraints.path_length:
                return False
    return True


def _certificate_ca_constraints(
    certificate: Certificate,
) -> tuple[x509.BasicConstraints, x509.KeyUsage] | None:
    """Return the mandatory CA extensions when both are present."""
    try:
        basic_constraints = certificate.extensions.get_extension_for_class(x509.BasicConstraints).value
        key_usage = certificate.extensions.get_extension_for_class(x509.KeyUsage).value
    except ExtensionNotFound:
        return None
    return basic_constraints, key_usage


def _certificate_datetime(certificate: Certificate, attribute: str) -> datetime:
    """Return a certificate validity datetime as a timezone-aware UTC value."""
    utc_attribute = f"{attribute}_utc"
    if hasattr(certificate, utc_attribute):
        return getattr(certificate, utc_attribute)
    return getattr(certificate, attribute).replace(tzinfo=timezone.utc)


def _has_seal_key_usage(certificate: Certificate) -> bool:
    """Return whether a leaf certificate permits electronic-signature operations."""
    try:
        key_usage = certificate.extensions.get_extension_for_class(x509.KeyUsage).value
    except ExtensionNotFound:
        return True
    return key_usage.digital_signature or key_usage.content_commitment


def _is_valid_leaf_certificate(certificate: Certificate) -> bool:
    """Return whether a certificate is a usable end-entity signing certificate."""
    try:
        basic_constraints = certificate.extensions.get_extension_for_class(x509.BasicConstraints).value
    except ExtensionNotFound:
        basic_constraints = None
    return (basic_constraints is None or not basic_constraints.ca) and _has_seal_key_usage(certificate)


def _validate_revocation(
    *,
    certificates: tuple[Certificate, ...],
    revocation_checker: RevocationChecker | None,
) -> tuple[RevocationStatus, str | None]:
    """Aggregate revocation results for every certificate and issuer pair."""
    if revocation_checker is None or len(certificates) < 2:
        return RevocationStatus.SKIPPED, None

    statuses: list[RevocationStatus] = []
    for certificate, issuer in zip(certificates, certificates[1:]):
        result = revocation_checker(certificate, issuer)
        if result.status is RevocationStatus.REVOKED:
            return result.status, result.reason or "A certificate in the signer chain was revoked"
        statuses.append(result.status)

    if RevocationStatus.UNKNOWN in statuses:
        return RevocationStatus.UNKNOWN, None
    if RevocationStatus.SKIPPED in statuses:
        return RevocationStatus.SKIPPED, None
    return RevocationStatus.GOOD, None


def _verify_signature(
    *,
    certificate: Certificate,
    signature: bytes,
    canonical_bytes: bytes,
    hash_algorithm: hashes.HashAlgorithm,
) -> bool:
    """Verify RSA PKCS#1/PSS or elliptic-curve signatures over canonical bytes."""
    return _verify_with_public_key(
        public_key=certificate.public_key(),
        signature=signature,
        data=canonical_bytes,
        hash_algorithm=hash_algorithm,
        rsa_paddings=(
            padding.PKCS1v15(),
            padding.PSS(mgf=padding.MGF1(hash_algorithm), salt_length=padding.PSS.DIGEST_LENGTH),
            padding.PSS(mgf=padding.MGF1(hash_algorithm), salt_length=padding.PSS.MAX_LENGTH),
        ),
    )


def _verify_with_public_key(
    *,
    public_key: RSAPublicKey | ec.EllipticCurvePublicKey,
    signature: bytes,
    data: bytes,
    hash_algorithm: hashes.HashAlgorithm,
    rsa_paddings: Iterable[AsymmetricPadding],
) -> bool:
    """Verify a signature with an RSA or elliptic-curve public key."""
    if isinstance(public_key, RSAPublicKey):
        for signature_padding in rsa_paddings:
            try:
                public_key.verify(
                    signature=signature,
                    data=data,
                    padding=signature_padding,
                    algorithm=hash_algorithm,
                )
                return True
            except (InvalidSignature, UnsupportedAlgorithm, ValueError):
                continue
        return False
    if isinstance(public_key, ec.EllipticCurvePublicKey):
        try:
            public_key.verify(
                signature=signature,
                data=data,
                signature_algorithm=ec.ECDSA(hash_algorithm),
            )
        except (InvalidSignature, UnsupportedAlgorithm, ValueError):
            return False
        return True
    return False


def _as_utc(value: datetime) -> datetime:
    """Normalize a datetime to timezone-aware UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _verification_failure(
    *,
    reason: str,
    detail: str,
    revocation_status: RevocationStatus = RevocationStatus.SKIPPED,
    chain_length: int = 0,
) -> SrtpVerificationResult:
    """Build a structured verification failure result."""
    return SrtpVerificationResult(
        is_valid=False,
        failure_reason=reason,
        failure_detail=detail,
        revocation_status=revocation_status,
        validated_certificate_chain_length=chain_length,
    )
