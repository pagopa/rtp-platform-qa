# Status-update callback test failures

## Test run summary

The selected status-update callback suite collected 11 tests and produced:

- **7 passed**
- **4 failed**
- Runtime: approximately 30 seconds
- Target environment used by the current configuration: UAT
- Callback URL configured in `config.yaml:76`:
  `https://api-rtp-cb.uat.cstar.pagopa.it/rtp/cb/v2/status-update`

The updated payload shape is accepted by the reason-based scenarios: ALAC, ARFR,
ARJR, AEXR, REPR, repeated ALAC, and unknown RTP handling passed. The failures
are separate issues involving resource lifecycle, an empty no-reason payload,
the PAID precondition, and certificate validation/environment configuration.

## 1. IRNR status update

### Test

`functional-tests/tests/callbacks_v2/test_RTP_status_update_callback.py::test_receive_status_update_callback_irnr`

### Intended scenario

The test models a debtor service provider reporting `IRNR` ("initial RTP not
received"):

1. The fixture activates a payer.
2. It creates an RTP through the GPD CREATE flow.
3. It verifies that the RTP starts in `SENT`.
4. It sends a status-update callback with reason code `IRNR`.
5. It expects the callback to return `200`.
6. It expects the RTP to transition to `ERROR_SEND`.
7. It then verifies that:
   - the RTP no longer appears in the notice-number search;
   - delivery status remains available;
   - delivery status is `PD_RTP_NOT_DELIVERED`;
   - `processingDate` is `None`.

The final checks are in
`functional-tests/tests/callbacks_v2/test_RTP_status_update_callback.py:107-137`.

### Failing assertion

The generic helper
`utils/status_update_test_helpers.py:35-41` always performs a resource GET
after the callback and requires:

```python
assert_response_code(get_response, 200, "GET RTP", expected_status)
assert get_response.json()["status"] == expected_status
```

For this run, the callback itself completed, but the resource GET returned
`404` instead of `200`.

### Root cause / violated assumption

`ERROR_SEND` is a purge state for the read API. The RTP is removed from the
resource read model, so `GET /rtps/{resourceId}` returning `404` is expected.
The test's own follow-up assertions already assume that the RTP is purged:
the notice-number query must return `200` with an empty list, while the
delivery-status endpoint must still return `200` with
`PD_RTP_NOT_DELIVERED`.

The generic helper is therefore incompatible with the IRNR lifecycle. This is
a test-helper/test-flow issue, not evidence that the callback transition failed.

### Recommended implementation direction

Use a separate assertion path for IRNR, or make the helper support an expected
resource GET status of `404`. The IRNR test should assert the purge and delivery
status directly rather than requiring the resource GET to remain readable.

## 2. Status update without a reason code

### Test

`functional-tests/tests/callbacks_v2/test_RTP_status_update_callback.py::test_receive_status_update_callback_without_reason_keeps_sent`

### Intended scenario

The test:

1. Creates an RTP in `SENT`.
2. Sends a status-update callback with `reason_code=None`.
3. Expects the callback to return `200`.
4. Expects the RTP to remain in `SENT`.

The assumption is that `StsRsnInf` is optional and that a callback without a
reason code is accepted as a no-op.

### Actual generated payload

`utils/dataset_status_update_callback.py:26-29,44-48` initializes an empty
transaction object when no reason is supplied. The resulting relevant
structure is:

```json
{
  "OrgnlPmtInfAndSts": [
    {
      "TxInfAndSts": [
        {}
      ]
    }
  ]
}
```

The callback endpoint returned `400` at
`utils/status_update_test_helpers.py:30`, before the helper performed the
follow-up status GET.

### Root cause / violated assumption

The implementation does not omit the transaction information entirely; it
sends an empty `TxInfAndSts` item. The live endpoint rejects that structure.
The updated cURL only demonstrates the reason-present form, where
`StsRsnInf` is an object containing `Rsn.Cd`.

The repository guide currently states that `StsRsnInf` is optional, but that
statement does not match the observed response from the configured endpoint.
The exact valid reasonless representation still needs to be confirmed against
the callback contract. Possible outcomes are:

- generate a different structurally valid no-reason body;
- update the test to match the endpoint contract if a reason is required;
- run the test against the intended environment if UAT and DEV have different
  validation rules.

The failure is directly related to the no-reason payload construction, but the
successful reason-based tests show that the new top-level `Document` and
object-shaped `StsRsnInf` changes are accepted.

## 3. AEXR conflict test with a PAID RTP

### Test

`functional-tests/tests/callbacks_v2/test_RTP_status_update_callback.py::test_receive_status_update_callback_aexr_conflicts_with_paid`

### Intended scenario

The test wants to verify that an `AEXR` callback conflicts with an RTP already
in `PAID`:

1. Create an RTP.
2. Send a GPD UPDATE with status `PAID`.
3. Confirm the RTP is in `PAID`.
4. Send an `AEXR` callback.
5. Expect the callback to return `400`.
6. Expect the RTP to remain `PAID`.

The test calls `make_status_update_rtp("PAID")` at
`test_RTP_status_update_callback.py:210`.

### Failing assertion

The fixture performs the setup in
`functional-tests/tests/callbacks_v2/conftest.py:51-85`. After the GPD UPDATE
returns the expected HTTP response, it immediately reads the RTP and asserts:

```python
assert update_get_response.json()["status"] == update_status
```

The actual response status was `RFC_SENT`, not `PAID`. The failure occurs in
the fixture at `conftest.py:85`, so the AEXR callback is never sent and the
expected `400` conflict assertion is never reached.

### Root cause / violated assumption

The fixture assumes that a GPD UPDATE with `status="PAID"` directly produces a
readable RTP in `PAID`. In the executed environment, that flow produced
`RFC_SENT`. The repository already contains a dedicated test documenting an
UPDATE PAID path resulting in `RFC_SENT`:

`functional-tests/tests/process_messages_sender/test_RTP_process_sender_UPDATE.py:89-114`.

Therefore, the test does not establish its required precondition. It is testing
the AEXR conflict logic only in name; the callback portion is not executed.

### Recommended implementation direction

The test needs a setup path that reliably produces a readable `PAID` RTP before
the callback. Options include:

- use the supported payment/status flow that reaches `PAID`;
- wait for the asynchronous state transition if `RFC_SENT` is only
  intermediate;
- use a fixture specifically designed to seed `PAID`;
- or change the scenario to validate the actual `RFC_SENT` behavior if that is
  the intended contract.

The expected callback response should not be changed from `400` until the
precondition is genuinely `PAID`.

## 4. Invalid certificate serial

### Test

`functional-tests/tests/callbacks_v2/test_RTP_status_update_callback.py::test_receive_status_update_callback_invalid_certificate_serial`

### Intended scenario

The test:

1. Creates an RTP in `SENT`.
2. Sends an ALAC status-update callback using the normal mock certificate and
   key from the fixture.
3. Adds this header:

```text
X-Client-Certificate-Serial: unregistered-status-update-serial
```

4. Expects the callback to return `403`.
5. If accepted, it would verify that the RTP remains `SENT`.

The API client does pass `extra_headers` through to `requests.post` in
`api/RTP_callback_api.py:58-69`; the header is not being dropped by the test
client.

### Failing assertion

The callback returned `200` instead of the expected `403`, so the test failed
at `utils/status_update_test_helpers.py:30`. The subsequent RTP status check
was not reached.

### Root cause / violated assumption

The test assumes that the callback gateway treats the synthetic header as the
authoritative client-certificate identity and rejects the request when the
value is not registered. The request still uses a valid mTLS certificate, and
the observed UAT endpoint accepted it.

There is also an environment mismatch: the updated cURL targets the DEV
callback endpoint, while the current test configuration targets UAT. Unless an
environment variable overrides the value, the test is not exercising the same
endpoint as the supplied cURL.

This failure therefore indicates one of the following:

- UAT does not validate `X-Client-Certificate-Serial`;
- the header is ignored by the deployed gateway;
- certificate-serial validation is enabled only in DEV or another environment;
- the test must use an actually unregistered certificate rather than a valid
  certificate plus a fabricated header.

### Recommended implementation direction

Confirm which environment and authentication mechanism owns certificate
validation. Then either:

- point the test configuration at the intended DEV endpoint;
- use a real unregistered certificate identity;
- or remove/change the assertion if this header is not part of the deployed
  contract.

## Handoff summary

| Scenario | Failure category | Primary owner |
|---|---|---|
| IRNR | Generic helper expects a readable resource after purge | Test helper / test flow |
| No reason code | Empty `TxInfAndSts` object is rejected | Payload contract / generator |
| AEXR against PAID | Fixture does not establish `PAID`; actual state is `RFC_SENT` | Fixture / state setup |
| Invalid certificate serial | UAT accepts valid mTLS plus synthetic serial header; DEV/UAT mismatch | Environment / authentication contract |

The callback payload adaptation itself is partially validated by the seven
passing scenarios. The remaining failures should be addressed independently
rather than reverting the new top-level `Document`, object-shaped
`StsRsnInf`, or dashed `OrgnlMsgId` changes.

## Resolution applied in the QA suite

The callback tests were updated according to the exposed API contract:

- IRNR now accepts `404` for the resource GET after `ERROR_SEND`, while
  retaining the notice-number and delivery-status assertions.
- A missing reason code now expects the contractually invalid `400` response.
- The AEXR conflict scenario first moves the RTP to `USER_REJECTED` through an
  accepted callback flow, then verifies that AEXR returns `400` without changing
  that state.
- Certificate mismatch is represented by a callback BIC that does not match
  the certificate identity, rather than by adding an arbitrary serial header.

Verification after these changes:

```text
11 passed in 32.81s
```
