from api.debtor_activation_api import activate
from api.RTP_process_sender import send_gpd_message_v2
from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_C_ID
from utils.dataset_gpd_message import generate_gpd_message_payload
from utils.response_assertions_utils import assert_response_code
from utils.test_expectations import CREATE_EXPECTED_CODES, UPDATE_EXPECTED_CODES


def create_status_update_rtp(
    *,
    access_token: str,
    debtor_service_provider_token: str,
    fiscal_code: str,
) -> tuple[dict, str]:
    create_payload = generate_gpd_message_payload(
        fiscal_code=fiscal_code,
        operation="CREATE",
        status="VALID",
    )

    activation_response = activate(
        access_token=debtor_service_provider_token,
        payer_fiscal_code=fiscal_code,
        service_provider_id=DEBTOR_SERVICE_PROVIDER_C_ID,
    )
    assert_response_code(
        activation_response,
        201,
        "activation",
        "CREATE",
    )

    create_response = send_gpd_message_v2(
        access_token=access_token,
        message_payload=create_payload,
    )
    assert_response_code(
        create_response,
        CREATE_EXPECTED_CODES["VALID"],
        "GPD CREATE",
        "VALID",
    )

    resource_id = create_response.json().get("resourceId")
    assert isinstance(resource_id, str) and resource_id, "Missing resourceId in send GPD message response"
    return create_payload, resource_id


def update_status_update_rtp(
    *,
    access_token: str,
    fiscal_code: str,
    create_payload: dict,
    status: str,
) -> None:
    update_payload = generate_gpd_message_payload(
        fiscal_code=fiscal_code,
        operation="UPDATE",
        status=status,
        iuv=create_payload["iuv"],
        msg_id=create_payload["id"],
    )
    update_response = send_gpd_message_v2(
        access_token=access_token,
        message_payload=update_payload,
    )
    assert_response_code(
        update_response,
        UPDATE_EXPECTED_CODES[status],
        "GPD UPDATE",
        status,
    )
