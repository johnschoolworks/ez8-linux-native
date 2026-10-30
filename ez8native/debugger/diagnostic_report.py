"""Offline diagnostic report for observed Identify frames.

Reports byte-layout evidence only. It does not perform hardware I/O,
claim protocol success, or identify the MCU or cable firmware.
"""

from dataclasses import dataclass
from .identify_evidence import classify_identify_frame


@dataclass(frozen=True)
class IdentifyDiagnosticReport:
    raw_hex: str
    byte_length: int
    classification: str
    reason: str
    protocol_success: bool
    mcu_identified: bool
    firmware_identified: bool


def build_identify_report(frame: bytes) -> IdentifyDiagnosticReport:
    """Build a conservative, deterministic report from an offline frame."""
    result = classify_identify_frame(frame)

    if result.frame is None:
        raw_hex = ""
        byte_length = 0
    else:
        raw_hex = result.frame.hex(" ").upper()
        byte_length = len(result.frame)

    return IdentifyDiagnosticReport(
        raw_hex=raw_hex,
        byte_length=byte_length,
        classification=result.classification.value,
        reason=result.reason,
        protocol_success=False,
        mcu_identified=False,
        firmware_identified=False,
    )
