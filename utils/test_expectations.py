"""
Test expectations for GPD message operations.
Defines expected status codes and body presence for different operations and statuses.
"""

# CREATE
CREATE_EXPECTED_CODES = {
    "VALID": 200,
    "INVALID": 400,
    "PARTIALLY_PAID": 400,
    "PAID": 400,
    "PUBLISHED": 400,
    "EXPIRED": 400,
    "DRAFT": 400,
}

# UPDATE post CREATE VALID
UPDATE_EXPECTED_CODES = {
    "VALID": 200,
    "INVALID": 200,
    "PAID": 200,
    "EXPIRED": 200,
    "DRAFT": 200,
    "PARTIALLY_PAID": 400,
    "PUBLISHED": 400,
}

# UPDATE standalone (no prior CREATE)
UPDATE_BEFORE_CREATE_CODES = {
    "VALID": 200,
    "INVALID": 404,
    "PAID": 404,
    "EXPIRED": 404,
    "DRAFT": 404,
    "PARTIALLY_PAID": 400,
    "PUBLISHED": 400,
}

# UPDATE post CREATE VALID and DELETE
UPDATE_AFTER_CREATE_AND_DELETE_CODES = {
    "VALID": 422,
    "INVALID": 422,
    "PAID": 422,
    "EXPIRED": 422,
    "DRAFT": 422,
    "PARTIALLY_PAID": 400,
    "PUBLISHED": 400,
}

# DELETE post CREATE (status refers to the CREATE status)
DELETE_AFTER_CREATE_CODES = {
    "VALID": 200,
    "INVALID": 404,
    "PARTIALLY_PAID": 404,
    "PAID": 404,
    "PUBLISHED": 404,
    "EXPIRED": 404,
    "DRAFT": 404,
}

# DELETE post CREATE VALID and UPDATE (status refers to the UPDATE status)
DELETE_AFTER_UPDATE_CODES = {
    "VALID": 200,
    "PARTIALLY_PAID": 200,
    "PUBLISHED": 200,
    "INVALID": 422,
    "PAID": 422,
    "EXPIRED": 422,
    "DRAFT": 422,
}

# DELETE post standalone UPDATE (status refers to the UPDATE status)
DELETE_AFTER_UPDATE_STANDALONE_CODES = {
    "VALID": 200,
    "INVALID": 404,
    "PARTIALLY_PAID": 404,
    "PAID": 404,
    "PUBLISHED": 404,
    "EXPIRED": 404,
    "DRAFT": 404,
}

STATUSES_WITH_BODY = {"VALID"}


def should_have_body(status: str) -> bool:
    """Check if a status should return a non-empty body (for CREATE and simple DELETE scenarios)"""
    return status in STATUSES_WITH_BODY


def has_body_for_expected_code(expected_code: int) -> bool:
    """Return True if a 200 response is expected (i.e. a body should be present)"""
    return expected_code == 200


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
