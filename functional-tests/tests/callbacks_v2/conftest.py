from collections.abc import Callable

import pytest

from utils.rtp_status_update_helpers import wait_for_rtp_status
from utils.status_update_test_context import StatusUpdateRtpContext
from utils.status_update_fixture_helpers import create_status_update_rtp, update_status_update_rtp


@pytest.fixture
def make_status_update_rtp(
    rtp_consumer_access_token: str,
    debtor_service_provider_token_c: str,
    rtp_reader_access_token: str,
    random_fiscal_code: str,
    debtor_sp_mock_cert_key: tuple[str, str],
) -> Callable[[str | None], StatusUpdateRtpContext]:
    def _create(update_status: str | None = None) -> StatusUpdateRtpContext:
        create_payload, resource_id = create_status_update_rtp(
            access_token=rtp_consumer_access_token,
            debtor_service_provider_token=debtor_service_provider_token_c,
            fiscal_code=random_fiscal_code,
        )

        if update_status is not None:
            update_status_update_rtp(
                access_token=rtp_consumer_access_token,
                fiscal_code=random_fiscal_code,
                create_payload=create_payload,
                status=update_status,
            )

        wait_for_rtp_status(
            reader_token=rtp_reader_access_token,
            resource_id=resource_id,
            expected_status=update_status or "SENT",
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
