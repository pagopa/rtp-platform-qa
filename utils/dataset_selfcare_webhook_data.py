from datetime import timedelta

from utils.datetime_utils import generate_utc_timestamp

SC_DELEGATIONS_TOPIC = "SC-Delegations"
SELFCARE_TENANT_ID = "AR"
SELFCARE_PRODUCT_ID = "prod-rtp"
SELFCARE_NOTIFICATION_ID = "6ae36f27300fdbc0e35d8b79"


def generate_selfcare_delegation_created_payload() -> dict:
    """SC-Delegations notification for a newly created (ACTIVE) delegation."""
    return _generate_selfcare_delegation_payload(
        status="ACTIVE",
        event_type="ADD",
        created_at=generate_utc_timestamp(),
        updated_at=None,
        closed_at=None,
    )


def generate_selfcare_delegation_deleted_payload() -> dict:
    """SC-Delegations notification for a delegation that has been DELETED."""
    closed_at = generate_utc_timestamp()
    return _generate_selfcare_delegation_payload(
        status="DELETED",
        event_type="UPDATE",
        created_at=generate_utc_timestamp(timedelta(days=-1)),
        updated_at=closed_at,
        closed_at=closed_at,
    )


def _generate_selfcare_delegation_payload(
    status: str,
    event_type: str,
    created_at: str,
    updated_at: str | None,
    closed_at: str | None,
) -> dict:
    return {
        "tenantId": SELFCARE_TENANT_ID,
        "productId": SELFCARE_PRODUCT_ID,
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
            "productId": SELFCARE_PRODUCT_ID,
            "type": "PT",
            "status": status,
            "createdAt": created_at,
            "updatedAt": updated_at,
            "closedAt": closed_at,
            "isTest": False,
            "eventType": event_type,
        },
    }
