import pytest
from ez8native.debugger.mock_transport import MockTransport
from ez8native.debugger.transport import ShortReadError, TransportError


def test_mock_read_write_and_baud():
    m = MockTransport([b"abcdef"])
    m.write_all(b"\x80")
    assert m.read_exact(6) == b"abcdef"
    m.set_baud(57600)
    assert m.writes == [b"\x80"] and m.baud == 57600
    m.close()
    m.close()
    with pytest.raises(TransportError):
        m.write_all(b"x")


def test_mock_short_read_is_failure():
    with pytest.raises(ShortReadError):
        MockTransport([b"abc"]).read_exact(6)
    with pytest.raises(ShortReadError):
        MockTransport().read_exact(6)


@pytest.mark.parametrize("length", [-1, 0, 4097, 1.0, True])
def test_mock_invalid_lengths(length):
    with pytest.raises(ValueError):
        MockTransport().read_exact(length)


def test_mock_invalid_baud():
    with pytest.raises(ValueError):
        MockTransport().set_baud(115200)
