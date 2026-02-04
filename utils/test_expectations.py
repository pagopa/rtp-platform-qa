"""
Test expectations for GPD message operations.
Defines expected status codes and body presence for different operations and statuses.
"""

CREATE_EXPECTED_CODES = {
    'VALID': 200,
    'INVALID': 400,
    'PAID': 400,
    'PUBLISHED': 400,
    'EXPIRED': 400,
    'DRAFT': 400,
}

UPDATE_EXPECTED_CODES = {
    'VALID': 200,
    'INVALID': 200,
    'PAID': 200,
    'EXPIRED': 200,
    'DRAFT': 200,
    'PARTIALLY_PAID': 422,
    'PUBLISHED': 422,
}

DELETE_AFTER_CREATE_CODES = {
    'VALID': 200,
    'INVALID': 422,
    'PAID': 422,
    'PUBLISHED': 422,
    'EXPIRED': 422,
    'DRAFT': 422,
}

DELETE_AFTER_UPDATE_CODES = {
    'VALID': 200,
    'INVALID': 422,
    'PAID': 422,
    'EXPIRED': 422,
    'DRAFT': 422,
    'PARTIALLY_PAID': 422,
    'PUBLISHED': 422,
}

STATUSES_WITH_BODY = {'VALID'}


def should_have_body(status: str) -> bool:
    """Check if a status should return a non-empty body"""
    return status in STATUSES_WITH_BODY


def get_create_expected_code(status: str) -> int:
    """Get expected status code for CREATE operation"""
    return CREATE_EXPECTED_CODES.get(status, 400)


def get_update_expected_code(status: str) -> int:
    """Get expected status code for UPDATE operation"""
    return UPDATE_EXPECTED_CODES.get(status, 422)


def get_delete_after_create_code(status: str) -> int:
    """Get expected status code for DELETE after CREATE operation"""
    return DELETE_AFTER_CREATE_CODES.get(status, 422)


def get_delete_after_update_code(status: str) -> int:
    """Get expected status code for DELETE after UPDATE operation"""
    return DELETE_AFTER_UPDATE_CODES.get(status, 422)
