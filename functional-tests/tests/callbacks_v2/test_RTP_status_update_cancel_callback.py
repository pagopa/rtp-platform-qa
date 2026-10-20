import uuid
from collections.abc import Callable

import allure
import pytest

from utils.status_update_cancel_helpers import assert_status_update_cancel_transition
from utils.status_update_test_context import StatusUpdateRtpContext



@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Cancel Callback")
@allure.story("The debtor service provider accepts an expired RTP while a cancellation is pending")
@allure.title("An AEXR cancel status update transitions RFC_SENT to EXPIRED")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "status_update", "cancel")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_status_update_cancel_callback_aexr(
    make_status_update_cancel_rtp: Callable[[], StatusUpdateRtpContext],
) -> None:
    context = make_status_update_cancel_rtp()
    assert_status_update_cancel_transition(
        context=context,
        reason_code="AEXR",
        expected_status="EXPIRED",
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Cancel Callback")
@allure.story("The debtor service provider rejects the cancellation of an RTP already rejected by the debtor")
@allure.title("An RCAR cancel status update transitions RFC_SENT to CANCELLED_REJECTED")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "status_update", "cancel")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_status_update_cancel_callback_rcar(
    make_status_update_cancel_rtp: Callable[[], StatusUpdateRtpContext],
) -> None:
    context = make_status_update_cancel_rtp()
    assert_status_update_cancel_transition(
        context=context,
        reason_code="RCAR",
        expected_status="CANCELLED_REJECTED",
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Cancel Callback")
@allure.story("The debtor service provider reports that the cancellation was not accepted by the payer")
@allure.title("An RCNR cancel status update leaves RFC_SENT unchanged")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "status_update", "cancel")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_status_update_cancel_callback_rcnr_keeps_rfc_sent(
    make_status_update_cancel_rtp: Callable[[], StatusUpdateRtpContext],
) -> None:
    context = make_status_update_cancel_rtp()
    assert_status_update_cancel_transition(
        context=context,
        reason_code="RCNR",
        expected_status="RFC_SENT",
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Cancel Callback")
@allure.story("The debtor service provider reports that the cancellation was rejected by the payer's provider")
@allure.title("An RCPR cancel status update leaves RFC_SENT unchanged")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "status_update", "cancel")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_status_update_cancel_callback_rcpr_keeps_previous_state(
    make_status_update_cancel_rtp: Callable[[], StatusUpdateRtpContext],
) -> None:
    context = make_status_update_cancel_rtp()
    previous_status = "RFC_SENT"
    assert_status_update_cancel_transition(
        context=context,
        reason_code="RCPR",
        expected_status=previous_status,
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Cancel Callback")
@allure.story("The debtor service provider repeats an accepted cancel status update")
@allure.title("A repeated RCAR cancel status update is an idempotent no-op")
@allure.tag("functional", "happy_path", "rtp_callback", "v2", "status_update", "cancel")
@pytest.mark.callback
@pytest.mark.happy_path
def test_receive_status_update_cancel_callback_rcar_is_idempotent(
    make_status_update_cancel_rtp: Callable[[], StatusUpdateRtpContext],
) -> None:
    context = make_status_update_cancel_rtp()
    expected_response_code={0: 200, 1: 400}
    assert_status_update_cancel_transition(
        context=context,
        reason_code="RCAR",
        expected_status="CANCELLED_REJECTED",
        number_of_calls=2,
        expected_response_code=expected_response_code,
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Cancel Callback")
@allure.story("The debtor service provider reports an expired RTP after the cancellation was rejected")
@allure.title("An AEXR cancel status update conflicts with a CANCELLED_REJECTED RTP")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "status_update", "cancel")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_receive_status_update_cancel_callback_aexr_conflicts_with_cancelled_rejected(
    make_status_update_cancel_rtp: Callable[[], StatusUpdateRtpContext],
) -> None:
    context = make_status_update_cancel_rtp()
    assert_status_update_cancel_transition(
        context=context,
        reason_code="AEXR",
        expected_status="EXPIRED",
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Cancel Callback")
@allure.story("The debtor service provider sends a cancel status update without a reason code")
@allure.title("A cancel status update without StsRsnInf is rejected")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "status_update", "cancel")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_receive_status_update_cancel_callback_without_reason_keeps_rfc_sent(
    make_status_update_cancel_rtp: Callable[[], StatusUpdateRtpContext],
) -> None:
    context = make_status_update_cancel_rtp()
    assert_status_update_cancel_transition(
        context=context,
        reason_code=None,
        expected_status="RFC_SENT",
        expected_response_code=400,
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Cancel Callback")
@allure.story("The debtor service provider sends a cancel status update with a reason code not valid for cancellation")
@allure.title("A cancel status update with a non-cancellation reason code is rejected")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "status_update", "cancel")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_receive_status_update_cancel_callback_non_cancellation_reason_keeps_rfc_sent(
    make_status_update_cancel_rtp: Callable[[], StatusUpdateRtpContext],
) -> None:
    context = make_status_update_cancel_rtp()
    assert_status_update_cancel_transition(
        context=context,
        reason_code=None,
        expected_status="RFC_SENT",
        expected_response_code=400,
    )


@allure.epic("RTP Callback V2")
@allure.feature("RTP Status Update Cancel Callback")
@allure.story("The debtor service provider reports a cancel update for an unknown RTP")
@allure.title("A cancel status update callback for an unknown RTP is rejected")
@allure.tag("functional", "unhappy_path", "rtp_callback", "v2", "status_update", "cancel")
@pytest.mark.callback
@pytest.mark.unhappy_path
def test_receive_status_update_cancel_callback_unknown_rtp(
    make_status_update_cancel_rtp: Callable[[str | None], StatusUpdateRtpContext],
    debtor_sp_mock_cert_key: tuple[str, str],
) -> None:
    _resource_id = str(uuid.uuid4())
    context = make_status_update_cancel_rtp(provided_resource_id=_resource_id)
    assert_status_update_cancel_transition(
        context=context,
        reason_code=None,
        expected_status=None,
        expected_response_code=400,
    )
