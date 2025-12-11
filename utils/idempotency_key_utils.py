import uuid


def generate_idempotency_key(operation_slug: str, resource_id: str) -> str:
    """
    Generate idempotency-key UUIDv5 using:
      • namespace  = UUID(resource_id)
      • name       = operation_slug

    Args:
        operation_slug: operation slug
        resource_id:   RTP resource string UUID

    Returns:
        UUID string (v. 5) to use as idempotency-key.
    """
    namespace = uuid.UUID(resource_id)
    key = uuid.uuid5(namespace, operation_slug)
    return str(key)
