import uuid
from collections.abc import Callable

import allure
import pytest

from api.RTP_callback_api import srtp_status_update_callback
from api.RTP_get_api import get_rtp_by_notice_number, get_rtp_delivery_status
from utils.constants_secrets_helper import DEBTOR_SERVICE_PROVIDER_C_ID
from utils.dataset_status_update_callback import generate_status_update_callback_data
from utils.response_assertions_utils import assert_response_code
from utils.status_update_test_context import StatusUpdateRtpContext
from utils.status_update_test_helpers import assert_status_update_transition

_STATUS_NOT_DELIVERED = "PD_RTP_NOT_DELIVERED"


@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Callback")
@allure.story("The debtor service provider accepts an RTP through a status update callback")
@allure.title("An ALAC status update transitions SENT to USER_ACCEPTED")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "status_update")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_status_update_callback_alac(
    make_status_update_rtp: Callable[[str | None], StatusUpdateRtpContext],
) -> None:
    context = make_status_update_rtp(None)
    assert_status_update_transition(
        context=context,
        reason_code="ALAC",
        expected_status="USER_ACCEPTED",
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Callback")
@allure.story("The debtor service provider rejects an RTP already rejected by the debtor")
@allure.title("An ARFR status update transitions SENT to USER_REJECTED")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "status_update")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_status_update_callback_arfr(
    make_status_update_rtp: Callable[[str | None], StatusUpdateRtpContext],
) -> None:
    context = make_status_update_rtp(None)
    assert_status_update_transition(
        context=context,
        reason_code="ARFR",
        expected_status="USER_REJECTED",
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Callback")
@allure.story("The debtor service provider rejects an RTP already rejected by the service provider")
@allure.title("An ARJR status update transitions SENT to REJECTED")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "status_update")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_status_update_callback_arjr(
    make_status_update_rtp: Callable[[str | None], StatusUpdateRtpContext],
) -> None:
    context = make_status_update_rtp(None)
    assert_status_update_transition(
        context=context,
        reason_code="ARJR",
        expected_status="REJECTED",
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Callback")
@allure.story("The debtor service provider reports an expired RTP")
@allure.title("An AEXR status update transitions SENT to EXPIRED")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "status_update")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_status_update_callback_aexr(
    make_status_update_rtp: Callable[[str | None], StatusUpdateRtpContext],
) -> None:
    context = make_status_update_rtp(None)
    assert_status_update_transition(
        context=context,
        reason_code="AEXR",
        expected_status="EXPIRED",
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Callback")
@allure.story("The debtor service provider reports that no initial RTP was received")
@allure.title("An IRNR status update transitions SENT to ERROR_SEND and marks delivery as lost")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "status_update")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_status_update_callback_irnr(
    make_status_update_rtp: Callable[[str | None], StatusUpdateRtpContext],
) -> None:
    context = make_status_update_rtp(None)
    assert_status_update_transition(
        context=context,
        reason_code="IRNR",
        expected_status="ERROR_SEND",
    )

    notice_response = get_rtp_by_notice_number(
        access_token=context.reader_access_token,
        notice_number=context.notice_number,
    )
    assert_response_code(
        notice_response,
        200,
        "GET RTP by notice number",
        "ERROR_SEND",
    )
    assert notice_response.json() == [], (
        f"Expected no RTP for notice number {context.notice_number} after ERROR_SEND, got {notice_response.text}"
    )

    delivery_response = get_rtp_delivery_status(
        access_token=context.delivery_status_access_token,
        notice_number=context.notice_number,
        payee_id=context.payee_id,
    )
    assert_response_code(
        delivery_response,
        200,
        "GET RTP delivery status",
        "ERROR_SEND",
    )
    delivery_body = delivery_response.json()
    assert delivery_body.get("status") == _STATUS_NOT_DELIVERED, (
        f"Expected delivery status {_STATUS_NOT_DELIVERED}, got {delivery_body.get('status')}"
    )
    assert delivery_body.get("processingDate") is None, (
        f"Expected no processing date for an undelivered RTP, got {delivery_body.get('processingDate')}"
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Callback")
@allure.story("The debtor service provider reports that an RTP is still being processed")
@allure.title("A REPR status update leaves SENT unchanged")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "status_update")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_status_update_callback_repr_keeps_sent(
    make_status_update_rtp: Callable[[str | None], StatusUpdateRtpContext],
) -> None:
    context = make_status_update_rtp(None)
    assert_status_update_transition(
        context=context,
        reason_code="REPR",
        expected_status="SENT",
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Callback")
@allure.story("The debtor service provider sends a status update without a reason code")
@allure.title("A status update without StsRsnInf leaves SENT unchanged")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "status_update")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_status_update_callback_without_reason_keeps_sent(
    make_status_update_rtp: Callable[[str | None], StatusUpdateRtpContext],
) -> None:
    context = make_status_update_rtp(None)
    assert_status_update_transition(
        context=context,
        reason_code=None,
        expected_status="SENT",
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Callback")
@allure.story("The debtor service provider repeats an accepted status update")
@allure.title("A repeated ALAC status update is an idempotent no-op")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "status_update")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_status_update_callback_alac_is_idempotent(
    make_status_update_rtp: Callable[[str | None], StatusUpdateRtpContext],
) -> None:
    context = make_status_update_rtp(None)
    assert_status_update_transition(
        context=context,
        reason_code="ALAC",
        expected_status="USER_ACCEPTED",
    )
    assert_status_update_transition(
        context=context,
        reason_code="ALAC",
        expected_status="USER_ACCEPTED",
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Callback")
@allure.story("The debtor service provider reports an expired RTP after it was paid")
@allure.title("An AEXR status update conflicts with a PAID RTP")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "status_update")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_receive_status_update_callback_aexr_conflicts_with_paid(
    make_status_update_rtp: Callable[[str | None], StatusUpdateRtpContext],
) -> None:
    context = make_status_update_rtp("PAID")
    assert_status_update_transition(
        context=context,
        reason_code="AEXR",
        expected_status="PAID",
        expected_response_code=400,
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Callback")
@allure.story("The debtor service provider reports an update for an unknown RTP")
@allure.title("A status update callback for an unknown RTP is rejected")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "status_update")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_receive_status_update_callback_unknown_rtp(
    debtor_sp_mock_cert_key: tuple[str, str],
) -> None:
    resource_id = str(uuid.uuid4())
    callback_data = generate_status_update_callback_data(
        bic=DEBTOR_SERVICE_PROVIDER_C_ID,
        resource_id=resource_id,
        original_msg_id=resource_id,
        reason_code="AEXR",
    )
    callback_response = srtp_status_update_callback(
        rtp_payload=callback_data,
        cert_path=debtor_sp_mock_cert_key[0],
        key_path=debtor_sp_mock_cert_key[1],
    )

    assert_response_code(
        callback_response,
        400,
        "status-update callback",
        "unknown RTP",
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Callback")
@allure.story("An unregistered certificate serial attempts a status update")
@allure.title("A status update callback with an invalid certificate serial is forbidden")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "status_update")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_receive_status_update_callback_invalid_certificate_serial(
    make_status_update_rtp: Callable[[str | None], StatusUpdateRtpContext],
) -> None:
    context = make_status_update_rtp(None)
    assert_status_update_transition(
        context=context,
        reason_code="ALAC",
        expected_status="SENT",
        expected_response_code=403,
        extra_headers={"X-Client-Certificate-Serial": "unregistered-status-update-serial"},
    )
