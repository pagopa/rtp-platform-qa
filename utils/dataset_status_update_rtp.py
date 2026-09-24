from utils.type_utils import JsonType


def generate_status_update_rtp_data(resource_id: str) -> JsonType:
    """Generate the rtp-sender status-update request payload."""
    return {"resourceId": resource_id}
