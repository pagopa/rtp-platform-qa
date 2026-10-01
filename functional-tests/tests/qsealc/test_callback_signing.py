import base64
from unittest.mock import patch

import allure
import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from requests import Response

from api.RTP_callback_api import (
    srtp_callback_v2,
    srtp_rfc_callback_v2,
)
from api.utils.endpoints import CALLBACK_URL_V2, RFC_CALLBACK_URL_V2
from api.utils.http_utils import CERT_PATH, HTTP_TIMEOUT, KEY_PATH
from utils.srtp_message_signing import build_canonical_representation
from utils.srtp_signature import SRTP_SIGNATURE_HEADER

V2_CALLBACK_FUNCTIONS = (
    (srtp_callback_v2, CALLBACK_URL_V2),
    (srtp_rfc_callback_v2, RFC_CALLBACK_URL_V2),
)


@allure.epic("QSealC message signing")
@allure.feature("Callback integration")
@allure.story("Transmit the exact signed callback body")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
@pytest.mark.parametrize(("callback_function", "callback_url"), V2_CALLBACK_FUNCTIONS)
def test_callback_helpers_sign_the_exact_prepared_body(
    callback_function,
    callback_url,
    qsealc_key_material,
    ds_08p_callback_payload,
    callback_body_factory,
) -> None:
    expected_body = callback_body_factory(
        method="POST",
        url=callback_url,
        payload=ds_08p_callback_payload,
    )
    response = Response()
    response.status_code = 200

    with patch("api.RTP_callback_api.requests.Session.send", return_value=response) as send:
        callback_response = callback_function(
            cert_path=CERT_PATH,
            key_path=KEY_PATH,
            rtp_payload=ds_08p_callback_payload,
            include_version_header=False,
            qsealc_key_material=qsealc_key_material,
        )

    prepared_request = send.call_args.kwargs["request"]
    assert callback_response is response, "Expected the callback helper to return the HTTP response"
    assert prepared_request.body == expected_body, "Expected the signed body to be the body sent on the wire"
    assert prepared_request.url == callback_url, "Expected the signature target URI to match the callback endpoint"

    canonical = build_canonical_representation(
        method=prepared_request.method,
        url=prepared_request.url,
        headers=prepared_request.headers,
        body=prepared_request.body,
    )
    qsealc_key_material.private_key.public_key().verify(
        signature=base64.b64decode(prepared_request.headers[SRTP_SIGNATURE_HEADER]),
        data=canonical,
        padding=PKCS1v15(),
        algorithm=hashes.SHA256(),
    )


@allure.epic("QSealC message signing")
@allure.feature("Callback integration")
@allure.story("Preserve unsigned callback behavior")
@pytest.mark.functional
@pytest.mark.happy_path
@pytest.mark.callback
def test_callback_helper_preserves_unsigned_request_behavior(ds_08p_callback_payload) -> None:
    response = Response()
    response.status_code = 200

    with patch("api.RTP_callback_api.requests.post", return_value=response) as post:
        callback_response = srtp_callback_v2(
            cert_path=CERT_PATH,
            key_path=KEY_PATH,
            rtp_payload=ds_08p_callback_payload,
            include_version_header=False,
        )

    assert callback_response is response, "Expected the callback helper to return the HTTP response"
    post.assert_called_once_with(
        cert=(CERT_PATH, KEY_PATH),
        url=CALLBACK_URL_V2,
        headers={},
        json=ds_08p_callback_payload,
        timeout=HTTP_TIMEOUT,
    )
