"""G3.5 offline regression tests for observed Identify frame."""

import pytest

from ez8native.debugger.hardware_identify import (
    HardwareIdentifyError,
    parse_hardware_identify,
)


def test_observed_frame():
    frame = bytes.fromhex("55 88 11 06 04 03")
    assert parse_hardware_identify(frame) == bytes.fromhex("06 04 03")


@pytest.mark.parametrize("frame", [
    b"",
    bytes.fromhex("55 88 11"),
    bytes.fromhex("00 88 11 06 04 03"),
    bytes.fromhex("55 88 11 06 04 03 00"),
])
def test_invalid_frame(frame):
    with pytest.raises(HardwareIdentifyError):
        parse_hardware_identify(frame)


def test_rejects_non_bytes():
    with pytest.raises(HardwareIdentifyError):
        parse_hardware_identify(bytearray.fromhex("55 88 11 06 04 03"))
