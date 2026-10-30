"""In-memory transport: all responses are synthetic test fixtures."""
from collections import deque
from .transport import Transport, TransportError, ShortReadError, TransportTimeoutError


class MockTransport(Transport):
    def __init__(self, responses=()):
        self._responses = deque()
        for response in responses:
            if type(response) is not bytes and type(response) is not TransportTimeoutError:
                raise TypeError("Mock responses must be bytes or synthetic timeout fixtures")
            self._responses.append(response)
        self.writes = []
        self.audit = []
        self.baud = None
        self.closed = False

    def _check_open(self):
        if self.closed:
            raise TransportError("mock transport closed")

    def write_all(self, data: bytes) -> None:
        self._check_open()
        if type(data) is not bytes or not data:
            raise ValueError("write_all expects nonempty bytes")
        self.writes.append(data)
        self.audit.append(("write", data))

    def read_exact(self, length: int) -> bytes:
        self._check_open()
        if type(length) is not int or not 1 <= length <= 4096:
            raise ValueError("length must be an integer in [1, 4096]")
        if not self._responses:
            raise ShortReadError("no synthetic response queued")
        response = self._responses.popleft()
        if type(response) is TransportTimeoutError:
            self.audit.append(("timeout", length))
            raise response
        if len(response) != length:
            raise ShortReadError(f"expected {length} synthetic bytes, got {len(response)}")
        self.audit.append(("read", response))
        return response

    def set_baud(self, rate: int) -> None:
        self._check_open()
        if type(rate) is not int or rate != 57600:
            raise ValueError("only offline candidate 57600 is supported")
        self.baud = rate
        self.audit.append(("baud", rate))

    def close(self) -> None:
        self.closed = True
