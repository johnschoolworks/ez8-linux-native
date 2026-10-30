import pytest
from ez8native.debugger.cable_protocol import (
    EVIDENCE, ProtocolError, encode_identify, parse_identify, encode_baud
)


def test_static_candidates():
    assert EVIDENCE == "STATIC_DLL"
    assert encode_identify() == b"\x80"
    assert encode_baud(57600) == b"\x00\x00\x14"
    assert parse_identify(b"\x01\x02\x03\x55\x88\x11") == b"\x01\x02\x03"


@pytest.mark.parametrize("response", [b"", b"\x55\x88\x11", b"\x00\x00\x00\x55\x88\x00", "invalid"])
def test_bad_identify_response(response):
    with pytest.raises(ProtocolError):
        parse_identify(response)


@pytest.mark.parametrize("baud", [9600, 19200, 38400, 115200, True, "57600"])
def test_unsupported_baud(baud):
    with pytest.raises(ProtocolError):
        encode_baud(baud)
