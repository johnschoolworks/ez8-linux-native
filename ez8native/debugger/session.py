"""Offline simulation of ONE static-DLL initialization branch."""
from enum import Enum, auto
from .cable_protocol import encode_identify, parse_identify, encode_baud
from .safety import require_mock, SafetyViolation


class State(Enum):
    DISCONNECTED = auto()
    MOCK_OPEN = auto()
    IDENTIFIED_MOCK = auto()
    BAUD_CONFIGURED_MOCK = auto()
    CLOSED = auto()
    ERROR = auto()


class MockSession:
    def __init__(self, transport):
        require_mock(transport)
        self.transport = transport
        self.state = State.DISCONNECTED
        self.identity_opaque = None
        self.last_error = None

    def connect(self):
        require_mock(self.transport)
        if self.state is not State.DISCONNECTED:
            raise SafetyViolation("connect is permitted only from DISCONNECTED")
        self.state = State.MOCK_OPEN
        try:
            self.transport.write_all(encode_identify())
            self.identity_opaque = parse_identify(self.transport.read_exact(6))
            self.state = State.IDENTIFIED_MOCK
            self.transport.write_all(encode_baud(57600))
            self.transport.set_baud(57600)
            self.state = State.BAUD_CONFIGURED_MOCK
        except Exception as exc:
            self.last_error = exc
            self.state = State.ERROR
            try:
                self.transport.close()
            except Exception:
                pass  # Preserve original failure.
            raise

    def close(self):
        self.transport.close()
        self.state = State.CLOSED
