import pytest
from ez8native.debugger.mock_transport import MockTransport
from ez8native.debugger.session import MockSession, State
from ez8native.debugger.ocd import Z8OCD
from ez8native.debugger.safety import SafetyViolation
from ez8native.debugger.cable_protocol import ProtocolError


def test_mock_session_known_branch():
    transport = MockTransport([b"\x01\x02\x03\x55\x88\x11"])
    session = MockSession(transport)
    session.connect()
    assert session.state is State.BAUD_CONFIGURED_MOCK
    assert transport.writes == [b"\x80", b"\x00\x00\x14"]
    assert transport.baud == 57600
    session.close()
    assert session.state is State.CLOSED


def test_invalid_response_fails_closed():
    transport = MockTransport([b"\x00" * 6])
    session = MockSession(transport)
    with pytest.raises(ProtocolError):
        session.connect()
    assert session.state is State.ERROR and transport.closed
    assert transport.writes == [b"\x80"]


def test_reconnect_rejected():
    session = MockSession(MockTransport([b"\x00" * 3 + b"\x55\x88\x11"]))
    session.connect()
    with pytest.raises(SafetyViolation):
        session.connect()


def test_reject_non_mock_transport():
    class FakePhysical:
        def write_all(self, data):
            raise AssertionError("must never be called")
    with pytest.raises(SafetyViolation):
        MockSession(FakePhysical())


def test_reject_mock_subclass():
    class UnsafeSubclass(MockTransport):
        pass
    with pytest.raises(SafetyViolation):
        MockSession(UnsafeSubclass())


@pytest.mark.parametrize("method,args", [
    ("read_id", ()), ("read_memory", (0, 1)), ("reset", ()),
    ("flash_unlock", ()), ("page_erase", (0,)),
    ("mass_erase", ()), ("program_flash", (b"x",)),
])
def test_ocd_operations_blocked(method, args):
    with pytest.raises(SafetyViolation):
        getattr(Z8OCD(), method)(*args)
