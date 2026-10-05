"""Shared test types for QSealC certificate fixtures."""

from dataclasses import dataclass
from datetime import datetime

from utils.cryptography_utils import QsealcKeyMaterial


@dataclass(frozen=True)
class QsealcTestChain:
    """Hold the generated QSealC chain and its validity metadata."""

    key_material: QsealcKeyMaterial
    root_certificate_pem: bytes
    valid_until: datetime
