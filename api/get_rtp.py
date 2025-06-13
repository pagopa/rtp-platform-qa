import uuid, requests

from config.configuration import config

GET_RTP_URL = config.rtp_creation_base_url_path + config.get_rtp_path

def get_rtp(access_token: str, rtp_id: str):
    url = GET_RTP_URL.format(rtpId=rtp_id)
    headers = {
        "Authorization": access_token,
        "Version": config.get_api_version,
        "RequestId": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }
    print(f"\n🕵️ GET {url}")
    print("   headers=", headers)
    resp = requests.get(url=url, headers=headers, timeout=config.default_timeout)
    print("   → status:", resp.status_code)
    print("   → body  :", resp.text, "\n")
    return resp
