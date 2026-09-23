from collections.abc import Callable

import pytest

from api.debtor_activation_api import activate
from api.RTP_get_api import get_rtp_v2
from api.RTP_process_sender import send_gpd_message_v2
from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_C_ID
from utils.dataset_gpd_message import generate_gpd_message_payload
from utils.response_assertions_utils import assert_response_code
from utils.status_update_test_context import StatusUpdateRtpContext
from utils.test_expectations import CREATE_EXPECTED_CODES, UPDATE_EXPECTED_CODES


@pytest.fixture
def make_status_update_rtp(
    rtp_consumer_access_token: str,
    debtor_service_provider_token_c: str,
    rtp_reader_access_token: str,
    random_fiscal_code: str,
    debtor_sp_mock_cert_key: tuple[str, str],
) -> Callable[[str | None], StatusUpdateRtpContext]:
    def _create(update_status: str | None = None) -> StatusUpdateRtpContext:
        create_payload = generate_gpd_message_payload(
            fiscal_code=random_fiscal_code,
            operation="CREATE",
            status="VALID",
        )

        activation_response = activate(
            access_token=debtor_service_provider_token_c,
            payer_fiscal_code=random_fiscal_code,
            service_provider_id=DEBTOR_SERVICE_PROVIDER_C_ID,
        )
        assert_response_code(
            activation_response,
            201,
            "activation",
            "CREATE",
        )

        create_response = send_gpd_message_v2(
            access_token=rtp_consumer_access_token,
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

        if update_status is not None:
            update_payload = generate_gpd_message_payload(
                fiscal_code=random_fiscal_code,
                operation="UPDATE",
                status=update_status,
                iuv=create_payload["iuv"],
                msg_id=create_payload["id"],
            )
            update_response = send_gpd_message_v2(
                access_token=rtp_consumer_access_token,
                message_payload=update_payload,
            )
            assert_response_code(
                update_response,
                UPDATE_EXPECTED_CODES[update_status],
                "GPD UPDATE",
                update_status,
            )

            update_get_response = get_rtp_v2(
                access_token=rtp_reader_access_token,
                rtp_id=resource_id,
            )
            assert_response_code(
                update_get_response,
                200,
                "GET RTP",
                update_status,
            )
            assert update_get_response.json()["status"] == update_status, (
                f"Expected RTP status {update_status}, got {update_get_response.json()['status']}"
            )
        else:
            initial_get_response = get_rtp_v2(
                access_token=rtp_reader_access_token,
                rtp_id=resource_id,
            )
            assert_response_code(
                initial_get_response,
                200,
                "GET RTP",
                "SENT",
            )
            assert initial_get_response.json()["status"] == "SENT", (
                f"Expected RTP status SENT before callback, got {initial_get_response.json()['status']}"
            )

        return StatusUpdateRtpContext(
            resource_id=resource_id,
            reader_access_token=rtp_reader_access_token,
            delivery_status_access_token=debtor_service_provider_token_c,
            certificate=debtor_sp_mock_cert_key[0],
            key=debtor_sp_mock_cert_key[1],
            notice_number=str(create_payload["nav"]),
            payee_id=str(create_payload["ec_tax_code"]),
        )

    return _create
