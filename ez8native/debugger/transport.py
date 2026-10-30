"""Transport contract; deliberately no serial or OS-device imports."""
from abc import ABC, abstractmethod


class TransportError(RuntimeError):
    pass


class ShortReadError(TransportError):
    pass


class TransportTimeoutError(TransportError):
    pass


class Transport(ABC):
    @abstractmethod
    def write_all(self, data: bytes) -> None: ...

    @abstractmethod
    def read_exact(self, length: int) -> bytes: ...

    @abstractmethod
    def set_baud(self, rate: int) -> None: ...

    @abstractmethod
    def close(self) -> None: ...
