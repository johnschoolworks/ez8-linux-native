"""G3.7-I offline evidence-classifier regression tests."""

import pytest

from ez8native.debugger.identify_evidence import (
    IdentifyEvidence,
    classify_identify_frame,
)


DLL_FRAME = bytes.fromhex("01 02 03 55 88 11")
OBSERVED_FRAME = bytes.fromhex("55 88 11 06 04 03")


def test_static_dll_layout_classified_without_protocol_claim():
    result = classify_identify_frame(DLL_FRAME)

    assert result.classification is IdentifyEvidence.STATIC_DLL_LAYOUT
    assert result.frame == DLL_FRAME
    assert "static DLL" in result.reason
    assert result.classification.value != "IDENTIFY_SUCCESS"


def test_alternate_observed_layout_classified():
    result = classify_identify_frame(OBSERVED_FRAME)

    assert (
        result.classification
        is IdentifyEvidence.HARDWARE_OBSERVED_ALTERNATE_LAYOUT
    )
    assert result.frame == OBSERVED_FRAME
    assert "alternate" in result.reason


@pytest.mark.parametrize("frame", [
    b"",
    b"\x55\x88\x11",
    bytes.fromhex("55 88 11 06 04 03 00"),
    bytes.fromhex("00 01 02 03 04 05"),
])
def test_unknown_or_wrong_length_frame_is_unresolved(frame):
    result = classify_identify_frame(frame)

    assert result.classification is IdentifyEvidence.UNRESOLVED
    assert result.frame == frame


@pytest.mark.parametrize("frame", [
    bytearray.fromhex("55 88 11 06 04 03"),
    "55 88 11 06 04 03",
    None,
])
def test_non_bytes_input_is_unresolved(frame):
    result = classify_identify_frame(frame)

    assert result.classification is IdentifyEvidence.UNRESOLVED
    assert result.frame is None


def test_classifier_does_not_mutate_input():
    frame = bytes.fromhex("55 88 11 06 04 03")
    before = frame[:]

    classify_identify_frame(frame)

    assert frame == before


def test_result_is_immutable():
    from dataclasses import FrozenInstanceError

    result = classify_identify_frame(DLL_FRAME)

    with pytest.raises(FrozenInstanceError):
        result.reason = "IDENTIFY_SUCCESS"


def test_alternate_layout_is_not_declared_protocol_success():
    result = classify_identify_frame(OBSERVED_FRAME)

    assert result.classification.value == (
        "HARDWARE_OBSERVED_ALTERNATE_LAYOUT"
    )
    assert result.classification.value != "HARDWARE_VERIFIED"
    assert result.classification.value != "IDENTIFY_SUCCESS"
