import pytest

from ez8native.debugger.trace_replay import (
    EVIDENCE, TraceMismatch, replay, success_fixture, timeout_fixture
)
from ez8native.debugger.session import State
from ez8native.debugger.transport import TransportTimeoutError


def test_d51_success_replay():
    result = replay(**success_fixture())
    assert result.state is State.BAUD_CONFIGURED_MOCK
    assert result.error_type is None
    assert result.evidence == "SYNTHETIC"
    assert EVIDENCE == "SYNTHETIC"


def test_d51_deterministic_replay():
    first = replay(**success_fixture())
    second = replay(**success_fixture())
    assert first == second


def test_d51_timeout_replay():
    result = replay(**timeout_fixture())
    assert result.state is State.ERROR
    assert result.error_type == "TransportTimeoutError"


def test_d51_short_read_replay():
    result = replay(
        [b"abc"],
        [("write", bytes.fromhex("80"))],
        State.ERROR,
        "ShortReadError",
    )
    assert result.state is State.ERROR


def test_d51_invalid_signature_replay():
    response = bytes(6)
    result = replay(
        [response],
        [("write", bytes.fromhex("80")), ("read", response)],
        State.ERROR,
        "ProtocolError",
    )
    assert result.error_type == "ProtocolError"


def test_d51_missing_response_replay():
    result = replay(
        [],
        [("write", bytes.fromhex("80"))],
        State.ERROR,
        "ShortReadError",
    )
    assert result.state is State.ERROR


@pytest.mark.parametrize("altered", [
    [("write", b"\\x81")],
    [("write", bytes.fromhex("80")), ("baud", 57600)],
    [],
])
def test_d51_wrong_trace_rejected(altered):
    fixture = success_fixture()
    fixture["expected_audit"] = altered
    with pytest.raises(TraceMismatch):
        replay(**fixture)


def test_d51_wrong_state_rejected():
    fixture = success_fixture()
    fixture["expected_state"] = State.ERROR
    with pytest.raises(TraceMismatch, match="state mismatch"):
        replay(**fixture)


def test_d51_wrong_error_rejected():
    fixture = timeout_fixture()
    fixture["expected_error"] = "ProtocolError"
    with pytest.raises(TraceMismatch, match="error mismatch"):
        replay(**fixture)


@pytest.mark.parametrize("event", [
    ("serial_open", "/dev/ttyUSB0"),
    ("reset", 1),
    ("erase", 1),
    ("write", "not bytes"),
    ("baud", True),
    ("timeout", 6.0),
    ("read", bytearray(b"x")),
    ("write",),
])
def test_d51_invalid_events_rejected(event):
    with pytest.raises((TraceMismatch, TypeError)):
        replay([], [event], State.ERROR, "ShortReadError")


def test_d51_invalid_state_type_rejected():
    with pytest.raises(TypeError):
        replay([], [], "ERROR")


def test_d51_invalid_responses_type_rejected():
    with pytest.raises(TypeError):
        replay("not a fixture", [], State.ERROR)


def test_d51_invalid_error_type_rejected():
    with pytest.raises(TypeError):
        replay([], [], State.ERROR, 123)


def test_d51_fixture_cannot_claim_hardware_verification():
    result = replay(**success_fixture())
    assert result.evidence != "HARDWARE_VERIFIED"
