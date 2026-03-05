import os

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


def get_eventhub_connection_string() -> str:
    keyvault_name = os.environ["KEYVAULT_NAME"]
    secret_name = os.environ["EVENTHUB_SECRET_NAME"]

    keyvault_url = f"https://{keyvault_name}.vault.azure.net"
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=keyvault_url, credential=credential)

    secret = client.get_secret(secret_name)
    return secret.value
