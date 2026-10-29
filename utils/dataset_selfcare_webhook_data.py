from config.configuration import secrets

SC_DELEGATIONS_TOPIC = "SC-Delegations"


def generate_selfcare_delegation_created_payload() -> dict:
    """SC-Delegations notification for a newly created (ACTIVE) delegation."""
    return _generate_selfcare_delegation_payload(
        status="ACTIVE",
        event_type="ADD",
        updated_at=None,
        closed_at=None,
    )


def generate_selfcare_delegation_deleted_payload() -> dict:
    """SC-Delegations notification for a delegation that has been DELETED."""
    return _generate_selfcare_delegation_payload(
        status="DELETED",
        event_type="UPDATE",
        updated_at="2026-10-20T08:30:00.000Z",
        closed_at="2026-10-20T08:30:00.000Z",
    )


def _generate_selfcare_delegation_payload(
    status: str, event_type: str, updated_at: str | None, closed_at: str | None
) -> dict:
    product_id = secrets.selfcare_webhook.product_id
    return {
        "tenantId": secrets.selfcare_webhook.tenant_id,
        "productId": product_id,
        "topic": SC_DELEGATIONS_TOPIC,
        "payload": {
            "id": "c3e8b1d0-5f2a-4a67-9b14-7e0d2c9f8a36",
            "delegationId": "6710b8e1f2a4c07b9d3e5a12",
            "from": "a1f4c6e2-7b3d-4e9a-8c51-2d6f0b9e3a74",
            "fromTaxCode": "80012345678",
            "fromType": "PA",
            "institutionFromName": "Comune di Valle Verde",
            "institutionFromRootName": None,
            "to": "f7b2d9a4-1c6e-4d38-a5f0-9e3b8c2d1a67",
            "toTaxCode": "09876543210",
            "toType": "PT",
            "institutionToName": "Tech Pagamenti S.r.l.",
            "productId": product_id,
            "type": "PT",
            "status": status,
            "createdAt": "2026-10-15T10:15:03.204Z",
            "updatedAt": updated_at,
            "closedAt": closed_at,
            "isTest": False,
            "eventType": event_type,
        },
    }
