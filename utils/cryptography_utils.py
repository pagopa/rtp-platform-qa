"""Utility helpers for encoding credentials and handling certificates/keys.

This module provides functions to:
- build HTTP Basic auth tokens from client credentials,
- convert PKCS#12 (.pfx) bundles to PEM-encoded certificate and key files,
- extract certificate serial numbers from PEM data.
"""

import base64
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.serialization import NoEncryption
from cryptography.hazmat.primitives.serialization import PrivateFormat
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from cryptography.x509 import load_pem_x509_certificate


def client_credentials_to_auth_token(client_id, client_secret):
    """Build a HTTP Basic Authorization header from client credentials.

    Args:
        client_id: OAuth client identifier.
        client_secret: OAuth client secret associated with the client.

    Returns:
        The value for the `Authorization` header (e.g. ``"Basic ..."``).
    """
    credentials = f"{client_id}:{client_secret}"
    base64_credentials = base64.b64encode(credentials.encode()).decode()
    return f"Basic {base64_credentials}"


def pfx_to_pem(base64_pfx, base64_password, cert_destination_path=None, key_destination_path=None):
    """Convert a base64-encoded PFX archive into PEM certificate and key files.

    Args:
        base64_pfx: Base64-encoded PKCS#12 (.pfx) content.
        base64_password: Base64-encoded password protecting the PFX.
        cert_destination_path: Filesystem path where the PEM certificate is written.
        key_destination_path: Filesystem path where the PEM private key is written.

    Returns:
        A tuple ``(cert_destination_path, key_destination_path)`` with the paths
        of the generated files.
    """

    pfx_data = base64.b64decode(base64_pfx)
    pfx_password = base64.b64decode(base64_password)

    private_key, certificate, _ = load_key_and_certificates(pfx_data, pfx_password)

    if certificate:
        os.makedirs(os.path.dirname(cert_destination_path), exist_ok=True)
        with open(cert_destination_path, 'wb+') as cert_file:
            cert_file.write(certificate.public_bytes(Encoding.PEM))

    if private_key:
        os.makedirs(os.path.dirname(key_destination_path), exist_ok=True)
        with open(key_destination_path, 'wb+') as key_file:
            key_file.write(private_key.private_bytes(
                Encoding.PEM,
                PrivateFormat.TraditionalOpenSSL,
                NoEncryption()
            ))

    return cert_destination_path, key_destination_path


def get_serial_from_pem(pem_data):
    """Extract the certificate serial number in hexadecimal from PEM data.

    Args:
        pem_data: Bytes containing a PEM-encoded X.509 certificate.

    Returns:
        The certificate serial number as a lowercase hexadecimal string.
    """

    cert = load_pem_x509_certificate(pem_data, default_backend())
    serial_int = cert.serial_number
    serial_hex = format(serial_int, 'x')

    return serial_hex
