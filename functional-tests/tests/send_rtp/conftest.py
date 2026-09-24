from collections.abc import Callable

import pytest

from api.debtor_activation_api import activate
from config.configuration import secrets
from utils.rtp_status_update_helpers import (
    CreatedRtpContext,
    StatusUpdateRtpContext,
    create_rtp_for_status_update_v2,
    update_rtp_status_v2,
)


@pytest.fixture
def status_update_rtp_resource_factory(
    debtor_service_provider_token_c: str,
    creditor_service_provider_token_a: str,
    rtp_reader_access_token: str,
) -> Callable[..., CreatedRtpContext]:
    def _create(
        *,
        payer_id: str,
        notice_number: str,
    ) -> CreatedRtpContext:
        """Activate a payer and create an RTP for a status-update test.

        The fixture returns this callback to tests that need a fresh RTP
        resource. Each invocation creates an isolated activation and RTP.
        """
        activation_response = activate(
            access_token=debtor_service_provider_token_c,
            payer_fiscal_code=payer_id,
            service_provider_id=secrets.debtor_service_provider_C.service_provider_id,
        )
        assert activation_response.status_code == 201, (
            f"Expected activation status 201, got {activation_response.status_code}: {activation_response.text}"
        )

        return create_rtp_for_status_update_v2(
            creditor_token=creditor_service_provider_token_a,
            reader_token=rtp_reader_access_token,
            payer_id=payer_id,
            notice_number=notice_number,
        )

    return _create


@pytest.fixture
def status_update_rtp_factory(
    status_update_rtp_resource_factory: Callable[..., CreatedRtpContext],
    creditor_service_provider_token_a: str,
    rtp_reader_access_token: str,
) -> Callable[..., StatusUpdateRtpContext]:
    def _create(
        *,
        payer_id: str,
        notice_number: str,
        expected_final_status: str | None,
    ) -> StatusUpdateRtpContext:
        created_context = status_update_rtp_resource_factory(
            payer_id=payer_id,
            notice_number=notice_number,
        )
        status_update_response, final_status = update_rtp_status_v2(
            creditor_token=creditor_service_provider_token_a,
            reader_token=rtp_reader_access_token,
            resource_id=created_context.resource_id,
            expected_final_status=expected_final_status,
        )
        return StatusUpdateRtpContext(
            resource_id=created_context.resource_id,
            initial_status=created_context.initial_status,
            final_status=final_status,
            status_update_response=status_update_response,
        )

    return _create
