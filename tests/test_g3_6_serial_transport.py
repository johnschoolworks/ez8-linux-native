"""G3.6 offline-only SerialTransport regression tests."""

import pytest

from ez8native.debugger.serial_transport import SerialTransport
from ez8native.debugger.transport import (
    TransportError,
    ShortReadError,
    TransportTimeoutError,
)


class FakeSerial:
    def __init__(self, **kwargs):
        self.settings = kwargs
        self.port = None
        self.dtr = None
        self.is_open = False
        self.rx = b""
        self.tx = []
        self.baudrate = kwargs["baudrate"]

    def open(self):
        self.is_open = True

    def write(self, data):
        self.tx.append(data)
        return len(data)

    def flush(self):
        pass

    def read(self, length):
        result = self.rx[:length]
        self.rx = self.rx[length:]
        return result

    def close(self):
        self.is_open = False


def factory(**kwargs):
    return FakeSerial(**kwargs)


def test_hardware_disabled_by_default():
    transport = SerialTransport("fake", serial_factory=factory)
    with pytest.raises(TransportError):
        transport.open()


def test_open_and_close():
    transport = SerialTransport(
        "fake", allow_hardware=True, serial_factory=factory
    )
    transport.open()
    assert transport._serial.is_open
    assert transport._serial.settings["rtscts"] is True
    assert transport._serial.dtr is False
    transport.close()
    assert transport._serial is None


def test_write():
    transport = SerialTransport(
        "fake", allow_hardware=True, serial_factory=factory
    )
    transport.open()
    fake = transport._serial
    transport.write(bytes.fromhex("80"))
    assert fake.tx == [bytes.fromhex("80")]
    transport.close()


def test_identify_response():
    transport = SerialTransport(
        "fake", allow_hardware=True, serial_factory=factory
    )
    transport.open()
    transport._serial.rx = bytes.fromhex("55 88 11 06 04 03")
    assert transport.read(6) == bytes.fromhex("55 88 11 06 04 03")
    transport.close()


def test_timeout():
    transport = SerialTransport(
        "fake", allow_hardware=True, serial_factory=factory
    )
    transport.open()
    with pytest.raises(TransportTimeoutError):
        transport.read(6)
    transport.close()


def test_short_read():
    transport = SerialTransport(
        "fake", allow_hardware=True, serial_factory=factory
    )
    transport.open()
    transport._serial.rx = b"\\x55"
    with pytest.raises(ShortReadError):
        transport.read(6)
    transport.close()


def test_baud_change():
    transport = SerialTransport(
        "fake", allow_hardware=True, serial_factory=factory
    )
    transport.open()
    transport.set_baud(38400)
    assert transport._serial.baudrate == 38400
    transport.close()


def test_closed_transport_rejected():
    transport = SerialTransport(
        "fake", allow_hardware=True, serial_factory=factory
    )
    with pytest.raises(TransportError):
        transport.write(bytes.fromhex("80"))


def test_abstract_transport_contract():
    from ez8native.debugger.transport import Transport

    assert issubclass(SerialTransport, Transport)
    assert not SerialTransport.__abstractmethods__


def test_abc_write_all_and_read_exact():
    transport = SerialTransport(
        "fake", allow_hardware=True, serial_factory=factory
    )
    transport.open()
    try:
        fake = transport._serial
        transport.write_all(bytes.fromhex("80"))
        assert fake.tx == [bytes.fromhex("80")]

        fake.rx = bytes.fromhex("55 88 11 06 04 03")
        assert transport.read_exact(6) == bytes.fromhex(
            "55 88 11 06 04 03"
        )
    finally:
        transport.close()


@pytest.mark.parametrize("length", [0, -1, 4097, True, 1.5])
def test_invalid_read_length(length):
    transport = SerialTransport(
        "fake", allow_hardware=True, serial_factory=factory
    )
    transport.open()
    try:
        with pytest.raises(ValueError):
            transport.read_exact(length)
    finally:
        transport.close()


def test_duplicate_open_rejected():
    transport = SerialTransport(
        "fake", allow_hardware=True, serial_factory=factory
    )
    transport.open()
    try:
        with pytest.raises(TransportError):
            transport.open()
    finally:
        transport.close()


def test_open_failure():
    class FailingSerial(FakeSerial):
        def open(self):
            raise OSError("injected open failure")

    transport = SerialTransport(
        "fake",
        allow_hardware=True,
        serial_factory=lambda **kw: FailingSerial(**kw),
    )
    with pytest.raises(TransportError):
        transport.open()


def test_short_write():
    class ShortWriteSerial(FakeSerial):
        def write(self, data):
            return len(data) - 1

    transport = SerialTransport(
        "fake",
        allow_hardware=True,
        serial_factory=lambda **kw: ShortWriteSerial(**kw),
    )
    transport.open()
    try:
        with pytest.raises(TransportTimeoutError):
            transport.write_all(bytes.fromhex("80"))
    finally:
        transport.close()


def test_write_failure():
    class FailingWriteSerial(FakeSerial):
        def write(self, data):
            raise OSError("injected write failure")

    transport = SerialTransport(
        "fake",
        allow_hardware=True,
        serial_factory=lambda **kw: FailingWriteSerial(**kw),
    )
    transport.open()
    try:
        with pytest.raises(TransportError):
            transport.write_all(bytes.fromhex("80"))
    finally:
        transport.close()


def test_close_failure():
    class FailingCloseSerial(FakeSerial):
        def close(self):
            raise OSError("injected close failure")

    transport = SerialTransport(
        "fake",
        allow_hardware=True,
        serial_factory=lambda **kw: FailingCloseSerial(**kw),
    )
    transport.open()
    with pytest.raises(TransportError):
        transport.close()
    assert transport._serial is None
