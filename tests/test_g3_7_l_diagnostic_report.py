"""G3.7-L offline diagnostic report tests."""

from dataclasses import FrozenInstanceError

import pytest

from ez8native.debugger.diagnostic_report import build_identify_report


def test_observed_frame_report_preserves_raw_order():
    frame = bytes.fromhex("06 04 03 55 88 11")
    report = build_identify_report(frame)

    assert report.raw_hex == "06 04 03 55 88 11"
    assert report.byte_length == 6
    # The existing classifier matches bytes 3..5 against the static
    # DLL signature. This is a layout classification, not protocol proof.
    assert report.classification == "STATIC_DLL_LAYOUT"
    assert report.protocol_success is False
    assert report.mcu_identified is False
    assert report.firmware_identified is False


def test_static_dll_layout_report():
    report = build_identify_report(
        bytes.fromhex("01 02 03 55 88 11")
    )

    assert report.raw_hex == "01 02 03 55 88 11"
    assert report.classification == "STATIC_DLL_LAYOUT"
    assert report.protocol_success is False


@pytest.mark.parametrize("frame", [
    b"",
    b"\x55\x88\x11",
    bytes.fromhex("00 01 02 03 04 05 06"),
])
def test_invalid_length_is_reported_without_protocol_claim(frame):
    report = build_identify_report(frame)

    assert report.byte_length == len(frame)
    assert report.protocol_success is False
    assert report.mcu_identified is False
    assert report.firmware_identified is False


def test_non_bytes_input_is_unresolved():
    report = build_identify_report(bytearray.fromhex("55 88 11 06 04 03"))

    assert report.classification == "UNRESOLVED"
    assert report.raw_hex == ""
    assert report.byte_length == 0
    assert report.protocol_success is False


def test_report_is_immutable():
    report = build_identify_report(bytes.fromhex("55 88 11 06 04 03"))

    with pytest.raises(FrozenInstanceError):
        report.protocol_success = True


def test_report_does_not_reorder_observed_frame():
    frame = bytes.fromhex("55 88 11 06 04 03")
    report = build_identify_report(frame)

    assert report.raw_hex == "55 88 11 06 04 03"
    assert report.classification == "HARDWARE_OBSERVED_ALTERNATE_LAYOUT"
