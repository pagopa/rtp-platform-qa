# from azure.identity import AzureCliCredential
# from azure.keyvault.secrets import SecretClient
# import os
#
# def get_eventhub_connection_string():
#     keyvault_name = os.environ["KEYVAULT_NAME"]
#     secret_name = os.environ["EVENTHUB_SECRET_NAME"]
#
#     keyvault_url = f"https://{keyvault_name}.vault.azure.net"
#     credential = AzureCliCredential()
#     client = SecretClient(vault_url=keyvault_url, credential=credential)
#
#     secret = client.get_secret(secret_name)
#     print(f"[KeyVault] Retrieved secret '{secret_name}' from '{keyvault_name}'")
#     return secret.value

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os

def get_eventhub_connection_string():
    keyvault_name = os.environ["KEYVAULT_NAME"]
    secret_name = os.environ["EVENTHUB_SECRET_NAME"]

    keyvault_url = f"https://{keyvault_name}.vault.azure.net"
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=keyvault_url, credential=credential)

    secret = client.get_secret(secret_name)
    print(f"[KeyVault] Retrieved secret '{secret_name}' from '{keyvault_name}'")
    return secret.value
