import uuid
import requests

from config.configuration import config

GET_RTP_URL = config.rtp_creation_base_url_path + config.get_rtp_path


def get_rtp(access_token: str, rtp_id: str):
    """
    Retrieve the details of an existing RTP via GET.
    """
    url = GET_RTP_URL.format(rtpId=rtp_id)
    headers = {
        "Authorization": f"{access_token}",
        "Version": config.get_api_version,
        "RequestId": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }
    return requests.get(url=url, headers=headers, timeout=config.default_timeout)
