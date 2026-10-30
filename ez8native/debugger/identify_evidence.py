"""Offline classification of observed Smart Cable Identify frames.

This module classifies byte layouts only. It does not establish protocol
validity, identify the MCU, or infer cable firmware versions.
"""

from dataclasses import dataclass
from enum import Enum


FRAME_LENGTH = 6
DLL_SIGNATURE = bytes.fromhex("55 88 11")


class IdentifyEvidence(str, Enum):
    STATIC_DLL_LAYOUT = "STATIC_DLL_LAYOUT"
    HARDWARE_OBSERVED_ALTERNATE_LAYOUT = (
        "HARDWARE_OBSERVED_ALTERNATE_LAYOUT"
    )
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class IdentifyEvidenceResult:
    classification: IdentifyEvidence
    frame: bytes | None
    reason: str


def classify_identify_frame(frame: bytes) -> IdentifyEvidenceResult:
    """Classify an observed six-byte frame without claiming protocol success.

    STATIC_DLL_LAYOUT:
        Bytes 3..5 match the signature found in static DLL analysis.

    HARDWARE_OBSERVED_ALTERNATE_LAYOUT:
        Bytes 0..2 match the signature from the alternate observed layout.

    UNRESOLVED:
        The frame has an unsupported type, length, or layout.

    This function performs no hardware I/O.
    """
    if type(frame) is not bytes:
        return IdentifyEvidenceResult(
            IdentifyEvidence.UNRESOLVED,
            None,
            "frame must be bytes",
        )

    if len(frame) != FRAME_LENGTH:
        return IdentifyEvidenceResult(
            IdentifyEvidence.UNRESOLVED,
            frame,
            "expected exactly six bytes",
        )

    dll_layout = frame[3:] == DLL_SIGNATURE
    observed_layout = frame[:3] == DLL_SIGNATURE

    if dll_layout and observed_layout:
        return IdentifyEvidenceResult(
            IdentifyEvidence.UNRESOLVED,
            frame,
            "ambiguous layout",
        )

    if dll_layout:
        return IdentifyEvidenceResult(
            IdentifyEvidence.STATIC_DLL_LAYOUT,
            frame,
            "matches static DLL candidate offsets 3..5",
        )

    if observed_layout:
        return IdentifyEvidenceResult(
            IdentifyEvidence.HARDWARE_OBSERVED_ALTERNATE_LAYOUT,
            frame,
            "matches alternate hardware-observed layout",
        )

    return IdentifyEvidenceResult(
        IdentifyEvidence.UNRESOLVED,
        frame,
        "no recognized signature layout",
    )
