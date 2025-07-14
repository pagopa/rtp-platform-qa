import uuid


def generate_idempotency_key(operation_slug: str, resource_id: str) -> str:
    """
    Generate idempotency key based on operation slug and resource ID.

    Args:
        operation_slug: The operation slug (e.g., '/sepa-request-to-pay-requests')
        resource_id: The RTP resource ID

    Returns:
        UUID string to be used as idempotency key
    """
    combined_string = f"{operation_slug}{resource_id}"
    name_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, combined_string)
    return str(name_uuid)