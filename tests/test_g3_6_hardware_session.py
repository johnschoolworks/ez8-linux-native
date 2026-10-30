"""G3.6-C offline Hardware Identify integration tests."""

import pytest

from ez8native.debugger.hardware_session import HardwareIdentifySession
from ez8native.debugger.mock_transport import MockTransport
from ez8native.debugger.hardware_identify import HardwareIdentifyError
from ez8native.debugger.transport import (
    TransportTimeoutError,
    ShortReadError,
)


def test_identify_observed_frame():
    transport = MockTransport(
        responses=[bytes.fromhex("55 88 11 06 04 03")]
    )
    session = HardwareIdentifySession(transport)
    assert session.identify() == bytes.fromhex("06 04 03")


def test_identify_bad_prefix():
    transport = MockTransport(
        responses=[bytes.fromhex("00 88 11 06 04 03")]
    )
    session = HardwareIdentifySession(transport)
    with pytest.raises(HardwareIdentifyError):
        session.identify()


def test_reject_non_transport():
    with pytest.raises(TypeError):
        HardwareIdentifySession(object())


def test_identify_empty_mock_queue():
    transport = MockTransport(responses=[])
    session = HardwareIdentifySession(transport)
    with pytest.raises(ShortReadError):
        session.identify()


def test_identify_timeout_propagation():
    class TimeoutTransport(MockTransport):
        def read_exact(self, length):
            raise TransportTimeoutError("injected timeout")

    transport = TimeoutTransport(responses=[])
    session = HardwareIdentifySession(transport)

    with pytest.raises(TransportTimeoutError):
        session.identify()


def test_identify_short_read():
    transport = MockTransport(
        responses=[bytes.fromhex("55 88 11")]
    )
    session = HardwareIdentifySession(transport)
    with pytest.raises(ShortReadError):
        session.identify()
