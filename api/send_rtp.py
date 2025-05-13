import requests

from config.configuration import config

SEND_RTP_URL = config.rtp_creation_base_url_path + config.send_rtp_path
SERVICE_PROVIDER_MOCK_URL = config.mock_service_provider_url


def send_rtp(access_token: str, rtp_payload):
    """API to post a rtp request
        :returns: the response of the call.
        :rtype: requests.Response
    """
    return requests.post(
        headers={
            'Authorization': f'{access_token}',
            'Version': 'v1'
        },
        url=SEND_RTP_URL,
        json=rtp_payload,
        timeout=config.default_timeout
    )


def send_rtp_to_mock(rtp_payload):
    return requests.post(
        url=SERVICE_PROVIDER_MOCK_URL,
        json=rtp_payload,
        timeout=config.default_timeout
    )
def send_rtp_to_cbi(access_token: str, rtp_payload, cert_path: str = None, key_path: str = None):
    """API to post an RTP request to the CBI service provider gateway using mutual TLS.

    Uses client certificate and key defined in configuration.
    Logs status code and response body for debugging.
    """
    headers = {
        'Authorization': f'{access_token}',
        'Version': 'v1',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    use_cert = cert_path or config.cert_path
    use_key = key_path or config.key_path

    resp = requests.post(
        url=config.cbi_send_url,
        headers=headers,
        json=rtp_payload,
        timeout=config.long_timeout,
        cert=(use_cert, use_key)
    )

    print(f">>> [send_rtp_to_cbi] status: {resp.status_code}")
    try:
        print(f">>> [send_rtp_to_cbi] body: {resp.json()}")
    except ValueError:
        print(f">>> [send_rtp_to_cbi] body text: {resp.text}")

    return resp