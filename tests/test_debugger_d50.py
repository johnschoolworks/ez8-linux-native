
import pytest
from ez8native.debugger.transport import (
    TransportError, ShortReadError, TransportTimeoutError
)
from ez8native.debugger.mock_transport import MockTransport
from ez8native.debugger.session import MockSession, State
from ez8native.debugger.safety import SafetyViolation
from ez8native.debugger.cable_protocol import (
    ProtocolError, encode_identify, encode_baud, parse_identify
)

def test_d50_static_evidence_vectors():
    assert encode_identify() == bytes.fromhex("80")
    assert encode_baud(57600) == bytes.fromhex("000014")
    for prefix in (bytes(3), bytes.fromhex("ff7f01")):
        assert parse_identify(prefix + bytes.fromhex("558811")) == prefix

@pytest.mark.parametrize("response", [
    b"", bytes(5), bytes(7),
    bytes.fromhex("000000558810"),
    bytes.fromhex("000000558711"),
    bytearray(6), None
])
def test_d50_malformed_response(response):
    with pytest.raises(ProtocolError):
        parse_identify(response)

@pytest.mark.parametrize("rate", [
    0, -1, 9600, 115200, 57600.0, True, "57600", None
])
def test_d50_invalid_baud(rate):
    with pytest.raises(ProtocolError):
        encode_baud(rate)

def test_d50_timeout_distinct_from_short_read():
    m = MockTransport([TransportTimeoutError("synthetic timeout")])
    with pytest.raises(TransportTimeoutError):
        m.read_exact(6)
    assert m.audit == [("timeout", 6)]
    with pytest.raises(ShortReadError):
        m.read_exact(6)

@pytest.mark.parametrize("response,exc", [
    (bytes(5), ShortReadError),
    (bytes(6), ProtocolError),
    (TransportTimeoutError("synthetic timeout"), TransportTimeoutError)
])
def test_d50_session_failure(response, exc):
    m = MockTransport([response])
    s = MockSession(m)
    with pytest.raises(exc):
        s.connect()
    assert s.state is State.ERROR
    assert isinstance(s.last_error, exc)
    assert m.closed
    assert m.writes == [bytes.fromhex("80")]
    s.close()
    assert s.state is State.CLOSED
    assert isinstance(s.last_error, exc)

def test_d50_closed_transport():
    m = MockTransport()
    m.close()
    s = MockSession(m)
    with pytest.raises(TransportError):
        s.connect()
    assert s.state is State.ERROR
    assert isinstance(s.last_error, TransportError)

@pytest.mark.parametrize("stage,expected", [
    ("identify", []),
    ("baud_command", [bytes.fromhex("80")]),
    ("host_baud", [bytes.fromhex("80"), bytes.fromhex("000014")])
])
def test_d50_injected_failure(monkeypatch, stage, expected):
    m = MockTransport([bytes.fromhex("010203558811")])
    original = MockTransport.write_all
    def fail_write(self, data):
        if stage == "identify" or (
            stage == "baud_command" and data == bytes.fromhex("000014")
        ):
            raise TransportError("synthetic write failure")
        return original(self, data)
    if stage != "host_baud":
        monkeypatch.setattr(MockTransport, "write_all", fail_write)
    else:
        def fail_baud(self, rate):
            raise TransportError("synthetic baud failure")
        monkeypatch.setattr(MockTransport, "set_baud", fail_baud)
    s = MockSession(m)
    with pytest.raises(TransportError):
        s.connect()
    assert s.state is State.ERROR and m.closed
    assert isinstance(s.last_error, TransportError)
    assert m.writes == expected

def test_d50_reject_transport_replacement():
    s = MockSession(MockTransport())
    s.transport = object()
    with pytest.raises(SafetyViolation):
        s.connect()

@pytest.mark.parametrize("value", [b"", bytearray(b"x"), "x", None])
def test_d50_invalid_write(value):
    with pytest.raises(ValueError):
        MockTransport().write_all(value)

@pytest.mark.parametrize("value", [0, -1, 4097, True, 1.5, "6"])
def test_d50_invalid_read_length(value):
    with pytest.raises(ValueError):
        MockTransport().read_exact(value)
