import json
from pathlib import Path
import pytest

from ez8native.debugger.event_replay import (
    EVIDENCE, EventReplay, ReplayMismatch
)
from ez8native.debugger.cable_protocol import parse_identify, ProtocolError

CORPUS = Path(__file__).parent / "fixtures/debugger/d52_synthetic_traces.json"


def load_cases():
    data = json.loads(CORPUS.read_text())
    assert data["schema_version"] == 1
    assert data["evidence"] == "SYNTHETIC"
    assert data["hardware_verified"] is False
    return data["cases"]


@pytest.mark.parametrize("case", load_cases(), ids=lambda c: c["id"])
def test_d52_corpus(case):
    p = EventReplay(case["events"])
    p.tx(bytes.fromhex("80"))
    outcome = case["outcome"]

    if outcome == "timeout":
        with pytest.raises(TimeoutError):
            p.rx(6)
    elif outcome == "short_read":
        with pytest.raises(EOFError):
            p.rx(6)
    else:
        response = p.rx(6)
        if outcome == "protocol_error":
            with pytest.raises(ProtocolError):
                parse_identify(response)
        else:
            assert parse_identify(response) == bytes.fromhex("010203")
            p.tx(bytes.fromhex("000014"))
            p.baud(57600)

    result = p.finish()
    assert result.evidence == EVIDENCE
    assert result.consumed == len(case["events"])


def test_d52_determinism():
    case = load_cases()[0]
    results = []
    for _ in range(2):
        p = EventReplay(case["events"])
        p.tx(bytes.fromhex("80"))
        p.rx(6)
        p.tx(bytes.fromhex("000014"))
        p.baud(57600)
        results.append(p.finish())
    assert results[0] == results[1]


def test_d52_wrong_tx_rejected():
    p = EventReplay(load_cases()[0]["events"])
    with pytest.raises(ReplayMismatch):
        p.tx(bytes.fromhex("81"))
    assert p.remaining == 4


def test_d52_wrong_order_rejected():
    p = EventReplay(load_cases()[0]["events"])
    with pytest.raises(ReplayMismatch):
        p.rx(6)
    assert p.remaining == 4


def test_d52_unconsumed_events_rejected():
    p = EventReplay(load_cases()[0]["events"])
    p.tx(bytes.fromhex("80"))
    with pytest.raises(ReplayMismatch):
        p.finish()


def test_d52_extra_event_rejected():
    p = EventReplay([])
    with pytest.raises(ReplayMismatch):
        p.tx(bytes.fromhex("80"))


def test_d52_wrong_baud_rejected():
    p = EventReplay([{"kind": "baud", "value": 57600}])
    with pytest.raises(ReplayMismatch):
        p.baud(115200)


@pytest.mark.parametrize("event", [
    {"kind": "serial_open", "value": "ttyUSB0"},
    {"kind": "reset", "value": 1},
    {"kind": "erase", "value": 1},
    {"kind": "flash", "value": 1},
    {"kind": "tx", "value": "zz"},
    {"kind": "rx", "value": ""},
    {"kind": "tx", "value": "8"},
    {"kind": "baud", "value": True},
    {"kind": "timeout", "value": 0},
    {"kind": "rx", "value": "80", "device": "ttyUSB0"},
])
def test_d52_invalid_event_rejected(event):
    with pytest.raises((ReplayMismatch, TypeError)):
        EventReplay([event])


def test_d52_rx_size_mismatch():
    p = EventReplay([{"kind": "rx", "value": "0102"}])
    with pytest.raises(ReplayMismatch):
        p.rx(6)
    assert p.remaining == 1


def test_d52_timeout_size_mismatch():
    p = EventReplay([{"kind": "timeout", "value": 6}])
    with pytest.raises(ReplayMismatch):
        p.rx(5)
    assert p.remaining == 1


def test_d52_short_read_length_validation():
    p = EventReplay([{"kind": "short_read", "value": 6}])
    with pytest.raises(ReplayMismatch):
        p.rx(6)
    assert p.remaining == 1


def test_d52_no_device_operations():
    assert not hasattr(EventReplay, "open")
    assert not hasattr(EventReplay, "reset")
    assert not hasattr(EventReplay, "erase")
    assert not hasattr(EventReplay, "program")
