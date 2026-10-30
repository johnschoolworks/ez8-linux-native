"""Offline-only synthetic Smart Cable protocol trace replay."""
from dataclasses import dataclass
from .mock_transport import MockTransport
from .session import MockSession, State
from .transport import TransportTimeoutError

EVIDENCE = "SYNTHETIC"


class TraceMismatch(ValueError):
    """The observed mock transcript differs from the expected fixture."""


@dataclass(frozen=True)
class TraceResult:
    state: State
    audit: tuple
    error_type: str | None
    evidence: str = EVIDENCE


def replay(responses, expected_audit, expected_state, expected_error=None):
    """Replay synthetic responses; never opens a device.

    Expected audit entries are tuples: (write, bytes), (read, bytes),
    (baud, 57600), or (timeout, 6).
    """
    if type(responses) not in (tuple, list):
        raise TypeError("responses must be a list or tuple")
    if type(expected_audit) not in (tuple, list):
        raise TypeError("expected_audit must be a list or tuple")
    if type(expected_state) is not State:
        raise TypeError("expected_state must be a State")
    if expected_error is not None and type(expected_error) is not str:
        raise TypeError("expected_error must be a string or None")

    allowed = {"write", "read", "baud", "timeout", "short_read"}
    for item in expected_audit:
        if type(item) is not tuple or len(item) != 2:
            raise TraceMismatch("invalid trace event structure")
        kind, value = item
        if type(kind) is not str or kind not in allowed:
            raise TraceMismatch("unsupported trace event")
        if kind in ("write", "read") and type(value) is not bytes:
            raise TraceMismatch("write/read event requires bytes")
        if kind in ("baud", "timeout", "short_read") and type(value) is not int:
            raise TraceMismatch("numeric event requires integer")

    transport = MockTransport(responses)
    session = MockSession(transport)
    error = None
    try:
        session.connect()
    except Exception as exc:
        error = type(exc).__name__

    actual = tuple(transport.audit)
    expected = tuple(expected_audit)
    result = TraceResult(session.state, actual, error)

    if actual != expected:
        raise TraceMismatch(
            f"trace mismatch: expected {expected!r}; observed {actual!r}"
        )
    if result.state is not expected_state:
        raise TraceMismatch(
            f"state mismatch: expected {expected_state.name}, "
            f"observed {result.state.name}"
        )
    if result.error_type != expected_error:
        raise TraceMismatch(
            f"error mismatch: expected {expected_error!r}, "
            f"observed {result.error_type!r}"
        )
    return result


def success_fixture():
    """A synthetic fixture, NOT a captured Smart Cable response."""
    response = bytes.fromhex("010203558811")
    return {
        "responses": [response],
        "expected_audit": [
            ("write", bytes.fromhex("80")),
            ("read", response),
            ("write", bytes.fromhex("000014")),
            ("baud", 57600),
        ],
        "expected_state": State.BAUD_CONFIGURED_MOCK,
        "expected_error": None,
    }


def timeout_fixture():
    """Synthetic timeout during the six-byte identity response."""
    return {
        "responses": [TransportTimeoutError("synthetic timeout")],
        "expected_audit": [
            ("write", bytes.fromhex("80")),
            ("timeout", 6),
        ],
        "expected_state": State.ERROR,
        "expected_error": "TransportTimeoutError",
    }
