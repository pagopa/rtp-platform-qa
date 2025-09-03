import uuid
import requests
from config.configuration import config

GET_RTP_URL = config.rtp_creation_base_url_path + config.get_rtp_path
GET_RTP_BY_NOTICE_NUMBER_URL = config.rtp_creation_base_url_path + config.get_rtp_by_notice_number_path

def get_rtp(access_token: str, rtp_id: str):
    url = GET_RTP_URL.format(rtpId=rtp_id)
    headers = {
        'Authorization': access_token,
        'Version': config.get_api_version,
        'RequestId': str(uuid.uuid4()),
        'Content-Type': 'application/json',
    }
    resp = requests.get(url=url, headers=headers, timeout=config.default_timeout)
    return resp


def get_rtp_by_notice_number(access_token: str, notice_number: str):
    if not access_token:
        raise ValueError("access_token cannot be None")
    
    if not notice_number:
        raise ValueError("notice_number cannot be None")
    
    params = {"noticeNumber": notice_number}
    
    headers = {
        'Authorization': access_token,
        'Version': config.get_api_version,
        'RequestId': str(uuid.uuid4()),
        'Content-Type': 'application/json',
    }
    
    resp = requests.get(url=GET_RTP_BY_NOTICE_NUMBER_URL, params=params, headers=headers, timeout=config.default_timeout)
    return resp
