"""Static DLL candidate bytes. NOT hardware-verified commands."""


class ProtocolError(ValueError):
    pass


EVIDENCE = "STATIC_DLL"


def encode_identify() -> bytes:
    return b"\x80"


def parse_identify(data: bytes) -> bytes:
    if type(data) is not bytes or len(data) != 6:
        raise ProtocolError("candidate identity response must be exactly 6 bytes")
    if data[3:] != b"\x55\x88\x11":
        raise ProtocolError("candidate identity response signature mismatch")
    return data[:3]  # Opaque: do not infer model, version, or capabilities.


def encode_baud(rate: int) -> bytes:
    if type(rate) is not int or rate != 57600:
        raise ProtocolError("only the offline 57600 candidate is supported")
    return b"\x00\x00\x14"
