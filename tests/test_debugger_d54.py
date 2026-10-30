"""D54 offline end-to-end validation. Synthetic evidence only."""

import json
from pathlib import Path

import pytest

from ez8native.debugger.offline_replay_session import (
    OfflineReplaySession, ReplayTransportAdapter,
)
from ez8native.debugger.event_replay import ReplayMismatch
from ez8native.debugger.transport import (
    TransportError, TransportTimeoutError, ShortReadError,
)
from ez8native.debugger.cable_protocol import ProtocolError
from ez8native.debugger.session import MockSession, State
from ez8native.debugger.safety import SafetyViolation


CORPUS = (
    Path(__file__).parent
    / "fixtures/debugger/d52_synthetic_traces.json"
)


def fixture(name):
    data = json.loads(CORPUS.read_text())
    assert data["schema_version"] == 1
    assert data["evidence"] == "SYNTHETIC"
    assert data["hardware_verified"] is False
    return next(
        case["events"]
        for case in data["cases"]
        if case["id"] == name
    )


def success():
    return [dict(event) for event in fixture("identify_success")]


def assert_failed(session, error):
    with pytest.raises(error) as caught:
        session.connect()
    assert session.state is State.ERROR
    assert session.last_error is caught.value
    assert session.transport_closed
    assert session.replay_result is None


def test_d54_complete_initialization():
    session = OfflineReplaySession(success())
    result = session.connect()
    assert session.state is State.BAUD_CONFIGURED_MOCK
    assert session.identity_opaque == bytes.fromhex("010203")
    assert session.remaining == 0
    assert result.consumed == 4
    assert result.evidence == "SYNTHETIC"
    assert session.last_error is None


def test_d54_success_then_close():
    session = OfflineReplaySession(success())
    session.connect()
    session.close()
    assert session.state is State.CLOSED
    assert session.transport_closed


@pytest.mark.parametrize("name,error", [
    ("identify_timeout", TransportTimeoutError),
    ("identify_short_read", ShortReadError),
    ("identify_bad_signature", ProtocolError),
])
def test_d54_corpus_failure(name, error):
    session = OfflineReplaySession(fixture(name))
    assert_failed(session, error)


@pytest.mark.parametrize("index,value", [
    (0, "81"),
    (1, "010203558812"),
    (2, "000015"),
    (3, 115200),
])
def test_d54_corrupt_trace(index, value):
    trace = success()
    trace[index]["value"] = value
    session = OfflineReplaySession(trace)

    if index == 1:
        assert_failed(session, ProtocolError)
    else:
        assert_failed(session, ReplayMismatch)


@pytest.mark.parametrize("index", [0, 1, 2, 3])
def test_d54_missing_event(index):
    trace = success()
    del trace[index]
    session = OfflineReplaySession(trace)
    assert_failed(session, ReplayMismatch)


@pytest.mark.parametrize("event", [
    {"kind": "tx", "value": "ff"},
    {"kind": "rx", "value": "010203558811"},
    {"kind": "baud", "value": 57600},
])
def test_d54_trailing_event_rejected(event):
    trace = success()
    trace.append(event)
    session = OfflineReplaySession(trace)
    assert_failed(session, ReplayMismatch)
    assert session.remaining == 1


def test_d54_no_false_success_after_timeout():
    session = OfflineReplaySession(fixture("identify_timeout"))
    assert_failed(session, TransportTimeoutError)
    assert session.identity_opaque is None


def test_d54_no_false_success_after_short_read():
    session = OfflineReplaySession(fixture("identify_short_read"))
    assert_failed(session, ShortReadError)
    assert session.identity_opaque is None


def test_d54_no_false_success_after_protocol_error():
    session = OfflineReplaySession(fixture("identify_bad_signature"))
    assert_failed(session, ProtocolError)
    assert session.identity_opaque is None


def test_d54_no_reconnect_after_success():
    session = OfflineReplaySession(success())
    session.connect()
    with pytest.raises(TransportError):
        session.connect()
    assert session.state is State.BAUD_CONFIGURED_MOCK


def test_d54_no_reconnect_after_failure():
    session = OfflineReplaySession(fixture("identify_timeout"))
    assert_failed(session, TransportTimeoutError)
    with pytest.raises(TransportError):
        session.connect()
    assert session.state is State.ERROR


def test_d54_adapter_closed_operations_rejected():
    adapter = ReplayTransportAdapter(success())
    adapter.close()

    with pytest.raises(TransportError):
        adapter.write_all(bytes.fromhex("80"))
    with pytest.raises(TransportError):
        adapter.read_exact(6)
    with pytest.raises(TransportError):
        adapter.set_baud(57600)
    with pytest.raises(TransportError):
        adapter.finish()


def test_d54_d50_boundary_still_enforced():
    adapter = ReplayTransportAdapter(success())
    with pytest.raises(SafetyViolation):
        MockSession(adapter)


def test_d54_replay_determinism():
    results = []
    for _ in range(5):
        session = OfflineReplaySession(success())
        result = session.connect()
        results.append((
            result,
            session.identity_opaque,
            session.state,
            session.remaining,
        ))
    assert all(item == results[0] for item in results)


def test_d54_no_physical_device_interface():
    for cls in (ReplayTransportAdapter, OfflineReplaySession):
        for name in (
            "open", "reset", "erase", "flash",
            "program", "connect_serial",
        ):
            assert not hasattr(cls, name)
