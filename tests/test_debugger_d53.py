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

CORPUS = Path(__file__).parent / "fixtures/debugger/d52_synthetic_traces.json"


def cases():
    data = json.loads(CORPUS.read_text())
    assert data["evidence"] == "SYNTHETIC"
    assert data["hardware_verified"] is False
    return {case["id"]: case for case in data["cases"]}


def events(name):
    return cases()[name]["events"]


def test_d53_success():
    session = OfflineReplaySession(events("identify_success"))
    result = session.connect()
    assert session.state is State.BAUD_CONFIGURED_MOCK
    assert session.identity_opaque == bytes.fromhex("010203")
    assert result.evidence == "SYNTHETIC"
    assert result.consumed == 4
    assert session.remaining == 0
    assert session.last_error is None
    session.close()
    assert session.state is State.CLOSED


@pytest.mark.parametrize("name,error", [
    ("identify_timeout", TransportTimeoutError),
    ("identify_short_read", ShortReadError),
    ("identify_bad_signature", ProtocolError),
])
def test_d53_failure_cases(name, error):
    session = OfflineReplaySession(events(name))
    with pytest.raises(error) as caught:
        session.connect()
    assert session.state is State.ERROR
    assert session.last_error is caught.value
    assert session.transport_closed


def test_d53_wrong_tx():
    bad = [dict(e) for e in events("identify_success")]
    bad[0]["value"] = "81"
    session = OfflineReplaySession(bad)
    with pytest.raises(ReplayMismatch):
        session.connect()
    assert session.state is State.ERROR
    assert session.transport_closed


def test_d53_wrong_baud():
    bad = [dict(e) for e in events("identify_success")]
    bad[-1]["value"] = 115200
    session = OfflineReplaySession(bad)
    with pytest.raises(ReplayMismatch):
        session.connect()
    assert session.state is State.ERROR
    assert session.transport_closed


def test_d53_unconsumed_trace():
    bad = [dict(e) for e in events("identify_success")]
    bad.append({"kind": "tx", "value": "ff"})
    session = OfflineReplaySession(bad)
    with pytest.raises(ReplayMismatch):
        session.connect()
    assert session.state is State.ERROR
    assert session.remaining == 1
    assert session.transport_closed


def test_d53_reconnect_rejected():
    session = OfflineReplaySession(events("identify_success"))
    session.connect()
    with pytest.raises(TransportError):
        session.connect()


def test_d53_closed_adapter_rejected():
    adapter = ReplayTransportAdapter(events("identify_success"))
    adapter.close()
    with pytest.raises(TransportError):
        adapter.write_all(bytes.fromhex("80"))
    with pytest.raises(TransportError):
        adapter.read_exact(6)
    with pytest.raises(TransportError):
        adapter.finish()


def test_d53_d50_mock_boundary_preserved():
    adapter = ReplayTransportAdapter(events("identify_success"))
    with pytest.raises(SafetyViolation):
        MockSession(adapter)


def test_d53_determinism():
    results = []
    for _ in range(3):
        session = OfflineReplaySession(events("identify_success"))
        results.append((
            session.connect(),
            session.identity_opaque,
            session.state,
        ))
    assert results[0] == results[1] == results[2]


def test_d53_no_device_methods():
    for cls in (OfflineReplaySession, ReplayTransportAdapter):
        for name in ("open", "reset", "erase", "program", "flash"):
            assert not hasattr(cls, name)
