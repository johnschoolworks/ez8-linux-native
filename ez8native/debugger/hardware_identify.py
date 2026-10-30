"""Hardware-observed Zilog Smart Cable Identify frame.

Evidence: G3.4-E physical serial transcript.
This parser performs no hardware I/O.
"""

class HardwareIdentifyError(ValueError):
    pass

PREFIX = bytes.fromhex("55 88 11")
FRAME_LENGTH = 6


def parse_hardware_identify(frame: bytes) -> bytes:
    """Return opaque 3-byte suffix from observed six-byte frame."""
    if type(frame) is not bytes:
        raise HardwareIdentifyError("frame must be bytes")
    if len(frame) != FRAME_LENGTH:
        raise HardwareIdentifyError("expected six bytes")
    if frame[:3] != PREFIX:
        raise HardwareIdentifyError("unexpected frame prefix")
    return frame[3:]
