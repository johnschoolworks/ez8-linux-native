"""Isolated synthetic session replay. Never opens physical devices."""

from .event_replay import EventReplay, ReplayMismatch
from .transport import (
    TransportError, TransportTimeoutError, ShortReadError,
)
from .cable_protocol import encode_identify, parse_identify, encode_baud
from .session import State


class ReplayTransportAdapter:
    """A standalone offline adapter, deliberately not a Transport subclass."""

    def __init__(self, events):
        self._replay = EventReplay(events)
        self.closed = False

    def _check_open(self):
        if self.closed:
            raise TransportError("replay adapter closed")

    def write_all(self, data):
        self._check_open()
        self._replay.tx(data)

    def read_exact(self, length):
        self._check_open()
        try:
            return self._replay.rx(length)
        except TimeoutError as exc:
            raise TransportTimeoutError(str(exc)) from exc
        except EOFError as exc:
            raise ShortReadError(str(exc)) from exc

    def set_baud(self, rate):
        self._check_open()
        self._replay.baud(rate)

    def finish(self):
        self._check_open()
        return self._replay.finish()

    @property
    def remaining(self):
        return self._replay.remaining

    def close(self):
        self.closed = True


class OfflineReplaySession:
    """One candidate initialization sequence driven by synthetic events."""

    def __init__(self, events):
        self._transport = ReplayTransportAdapter(events)
        self.state = State.DISCONNECTED
        self.identity_opaque = None
        self.last_error = None
        self.replay_result = None

    @property
    def remaining(self):
        return self._transport.remaining

    @property
    def transport_closed(self):
        return self._transport.closed

    def connect(self):
        if self.state is not State.DISCONNECTED:
            raise TransportError("replay connect requires DISCONNECTED")

        self.state = State.MOCK_OPEN
        try:
            self._transport.write_all(encode_identify())
            self.identity_opaque = parse_identify(
                self._transport.read_exact(6)
            )
            self.state = State.IDENTIFIED_MOCK
            self._transport.write_all(encode_baud(57600))
            self._transport.set_baud(57600)
            self.replay_result = self._transport.finish()
            self.state = State.BAUD_CONFIGURED_MOCK
            return self.replay_result
        except Exception as exc:
            self.last_error = exc
            self.state = State.ERROR
            self._transport.close()
            raise

    def close(self):
        self._transport.close()
        self.state = State.CLOSED
