"""Strict offline event-by-event replay; no physical I/O."""
from dataclasses import dataclass

EVIDENCE = "SYNTHETIC"
KINDS = frozenset({"tx", "rx", "baud", "timeout", "short_read"})


class ReplayMismatch(ValueError):
    pass


@dataclass(frozen=True)
class ReplayResult:
    consumed: int
    evidence: str = EVIDENCE


class EventReplay:
    """Consume a synthetic event stream in exact order."""

    def __init__(self, events):
        if type(events) not in (list, tuple):
            raise TypeError("events must be a list or tuple")
        validated = []
        for event in events:
            if type(event) is not dict or set(event) != {"kind", "value"}:
                raise ReplayMismatch("invalid event structure")
            kind, value = event["kind"], event["value"]
            if type(kind) is not str or kind not in KINDS:
                raise ReplayMismatch("unsupported event kind")
            if kind in ("tx", "rx"):
                if type(value) is not str:
                    raise ReplayMismatch("byte value must be hex")
                try:
                    data = bytes.fromhex(value)
                except ValueError as exc:
                    raise ReplayMismatch("invalid hex") from exc
                if not data or data.hex() != value.lower():
                    raise ReplayMismatch("noncanonical or empty hex")
            elif type(value) is not int or value <= 0:
                raise ReplayMismatch("invalid numeric event")
            validated.append((kind, value))
        self._events = tuple(validated)
        self._cursor = 0

    @property
    def remaining(self):
        return len(self._events) - self._cursor

    def _consume(self, kind, value):
        if self._cursor >= len(self._events):
            raise ReplayMismatch("unexpected event after trace end")
        expected = self._events[self._cursor]
        if expected != (kind, value):
            raise ReplayMismatch(
                f"event {self._cursor}: expected {expected!r}, "
                f"observed {(kind, value)!r}"
            )
        self._cursor += 1

    def tx(self, data):
        if type(data) is not bytes or not data:
            raise TypeError("tx requires nonempty bytes")
        self._consume("tx", data.hex())

    def rx(self, size):
        if type(size) is not int or not 1 <= size <= 4096:
            raise ValueError("invalid receive size")
        if self._cursor >= len(self._events):
            raise ReplayMismatch("missing receive event")
        kind, value = self._events[self._cursor]
        if kind == "timeout":
            self._consume("timeout", size)
            raise TimeoutError("synthetic replay timeout")
        if kind == "short_read":
            if value >= size:
                raise ReplayMismatch("short_read must be shorter than request")
            self._consume("short_read", value)
            raise EOFError("synthetic replay short read")
        if kind != "rx":
            raise ReplayMismatch("expected receive event")
        data = bytes.fromhex(value)
        if len(data) != size:
            raise ReplayMismatch("receive length mismatch")
        self._consume("rx", value)
        return data

    def baud(self, rate):
        if type(rate) is not int:
            raise TypeError("baud must be integer")
        self._consume("baud", rate)

    def finish(self):
        if self.remaining:
            raise ReplayMismatch(f"{self.remaining} unconsumed events")
        return ReplayResult(self._cursor)
