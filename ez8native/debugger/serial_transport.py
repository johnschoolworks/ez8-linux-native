"""Opt-in serial transport for Zilog Smart Cable.

No port is opened during construction or module import.
Hardware access requires allow_hardware=True and explicit open().
"""

from .transport import (
    Transport,
    TransportError,
    ShortReadError,
    TransportTimeoutError,
)


class SerialTransport(Transport):
    def __init__(
        self,
        port,
        *,
        baudrate=57600,
        timeout=1.5,
        allow_hardware=False,
        serial_factory=None,
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.allow_hardware = allow_hardware
        self.serial_factory = serial_factory
        self._serial = None

    def open(self):
        if not self.allow_hardware:
            raise TransportError("Hardware access not authorized")
        if self._serial is not None:
            raise TransportError("Transport already open")

        factory = self.serial_factory
        if factory is None:
            import serial
            factory = serial.Serial

        try:
            connection = factory(
                port=None,
                baudrate=self.baudrate,
                bytesize=8,
                parity="N",
                stopbits=1,
                timeout=self.timeout,
                write_timeout=self.timeout,
                rtscts=True,
                dsrdtr=False,
                xonxoff=False,
                exclusive=True,
            )
            connection.dtr = False
            connection.port = self.port
            connection.open()
            self._serial = connection
        except Exception as exc:
            try:
                if "connection" in locals():
                    connection.close()
            except Exception:
                pass
            raise TransportError("Serial open failed") from exc

    def _require_open(self):
        if self._serial is None:
            raise TransportError("Serial transport not open")
        return self._serial

    def write(self, data: bytes) -> None:
        serial = self._require_open()
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        try:
            written = serial.write(data)
            if written != len(data):
                raise TransportTimeoutError("Incomplete serial write")
            serial.flush()
        except TransportTimeoutError:
            raise
        except Exception as exc:
            raise TransportError("Serial write failed") from exc

    def read(self, length: int) -> bytes:
        serial = self._require_open()
        if type(length) is not int or not 1 <= length <= 4096:
            raise ValueError("length must be an integer in [1, 4096]")
        try:
            data = serial.read(length)
        except Exception as exc:
            raise TransportError("Serial read failed") from exc
        if len(data) == 0:
            raise TransportTimeoutError("Serial read timeout")
        if len(data) != length:
            raise ShortReadError("Incomplete serial response")
        return data

    def write_all(self, data: bytes) -> None:
        """Write all bytes, raising on incomplete transmission."""
        self.write(data)

    def read_exact(self, length: int) -> bytes:
        """Read exactly length bytes or raise a transport error."""
        return self.read(length)

    def set_baud(self, rate: int) -> None:
        serial = self._require_open()
        if not isinstance(rate, int) or rate <= 0:
            raise ValueError("Invalid baud rate")
        try:
            serial.baudrate = rate
            self.baudrate = rate
        except Exception as exc:
            raise TransportError("Baud change failed") from exc

    def close(self) -> None:
        serial = self._serial
        self._serial = None
        if serial is not None:
            try:
                serial.close()
            except Exception as exc:
                raise TransportError("Serial close failed") from exc
