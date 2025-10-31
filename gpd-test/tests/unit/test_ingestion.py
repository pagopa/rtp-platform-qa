import asyncio
from typing import Any
from typing import cast

import pytest
from fastapi import HTTPException
from fastapi import UploadFile
from services.ingestion import send_file
from services.ingestion import send_message


class FakeProducerService:
    def __init__(self, fail: bool = False):
        self.sent = []
        self.fail = fail

    async def send_json(self, topic: str, payload: dict):

        await asyncio.sleep(0)
        if self.fail:
            raise RuntimeError('producer error')
        self.sent.append((topic, payload))


class FakeUploadFile:
    def __init__(self, lines: list[bytes]):
        self.file = lines


@pytest.mark.asyncio
async def test_send_message_success():
    producer = FakeProducerService()
    payload = {'id': 1, 'operation': 'CREATE', 'timestamp': 0}
    res = await send_message(cast(Any, producer), 'test-topic', payload, validate=True)
    assert res.status == 'success'
    assert producer.sent == [('test-topic', payload)]


@pytest.mark.asyncio
async def test_send_message_invalid_payload_raises_422():
    producer = FakeProducerService()
    payload = {'operation': 'CREATE', 'timestamp': 0}
    with pytest.raises(HTTPException) as exc:
        await send_message(cast(Any, producer), 'test-topic', payload, validate=True)
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_send_message_producer_error_raises_500():
    producer = FakeProducerService(fail=True)
    payload = {'id': 1, 'operation': 'CREATE', 'timestamp': 0}
    with pytest.raises(HTTPException) as exc:
        await send_message(cast(Any, producer), 'test-topic', payload, validate=True)
    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_send_file_mixed_lines_counts_sent_and_failed():
    producer = FakeProducerService()
    valid_line = b'{"id": 1, "operation": "CREATE", "timestamp": 0}\n'
    invalid_line = b'{invalid json}\n'
    fake_upload = FakeUploadFile([valid_line, invalid_line])

    res = await send_file(cast(Any, producer), 'test-topic', cast(UploadFile, fake_upload), rate=100, bulk=True)

    assert res.sent == 1
    assert res.failed == 1
    assert any(e.type for e in res.errors)
    assert producer.sent and producer.sent[0][0] == 'test-topic'
