def generate_status_update_rtp_data(resource_id: str) -> dict:
    """Generate the rtp-sender status-update request payload."""
    return {"resourceId": resource_id}
