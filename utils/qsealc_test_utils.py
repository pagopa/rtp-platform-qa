"""Shared test types for QSealC certificate fixtures."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from utils.cryptography_utils import QsealcKeyMaterial


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
