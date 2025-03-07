import base64
import os

from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.serialization import NoEncryption
from cryptography.hazmat.primitives.serialization import PrivateFormat
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates


def client_credentials_to_auth_token(client_id, client_secret):
    credentials = f"{client_id}:{client_secret}"
    base64_credentials = base64.b64encode(credentials.encode()).decode()
    return f"Basic {base64_credentials}"


def pfx_to_pem(base64_pfx, base64_password, cert_destination_path=None, key_destination_path=None):

    pfx_data = base64.b64decode(base64_pfx)
    pfx_password = base64.b64decode(base64_password)

    private_key, certificate, additional_certs = load_key_and_certificates(pfx_data, pfx_password)

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
