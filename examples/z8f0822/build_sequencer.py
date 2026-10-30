"""Build Z8F0822 three-LED GPIO sequencer, offline only."""

import argparse
import hashlib
import json
from pathlib import Path

from ez8native.firmware import build_firmware, load_vector_template
from ez8native.object_asm import assemble_object
from ez8native.vector_manifest import load_vector_manifest


SOURCE = """; Zilog F082 Evaluation Board
; D2 Red=PA0, D3 Green=PA1, D4 Yellow=PA2
; Active-low LEDs. Preserve PA3..PA7.
PORT_ADDR EQU %0FD0
PORT_CTL EQU %0FD1
PORT_OUT EQU %0FD3
.global MAIN

MAIN:
    ORX PORT_OUT, #%07

    LDX PORT_ADDR, #%02
    ANDX PORT_CTL, #%F8

    LDX PORT_ADDR, #%03
    ANDX PORT_CTL, #%F8

    LDX PORT_ADDR, #%01
    ANDX PORT_CTL, #%F8

SEQUENCE:
    ; Red on, green/yellow off
    ORX PORT_OUT, #%07
    ANDX PORT_OUT, #%FE
    CALL DELAY

    ; Green on, red/yellow off
    ORX PORT_OUT, #%07
    ANDX PORT_OUT, #%FD
    CALL DELAY

    ; Yellow on, red/green off
    ORX PORT_OUT, #%07
    ANDX PORT_OUT, #%FB
    CALL DELAY

    JR SEQUENCE

; Delay inherited from hardware-verified PA0 blink.
; Timing remains uncalibrated.
DELAY:
    LD R0, #32
DELAY_OUTER:
    LD R1, #0
DELAY_MIDDLE:
    LD R2, #0
DELAY_INNER:
    DEC R2
    JR NZ, DELAY_INNER
    DEC R1
    JR NZ, DELAY_MIDDLE
    DEC R0
    JR NZ, DELAY_OUTER
    RET
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    here = Path(__file__).resolve().parent

    startup = assemble_object(
        (here / "startup.asm").read_text(),
        section="STARTUP",
    )
    main_object = assemble_object(SOURCE, section="CODE")

    text, placed, symbols, _ = build_firmware(
        [startup, main_object],
        load_vector_template(here / "reset-only.hex"),
        vector_manifest=load_vector_manifest(
            here / "manifests/reset-only.json"
        ),
    )

    code = bytes.fromhex(main_object["sections"][0]["data"])
    end = placed["m1:CODE"] + len(code)

    if end > 512:
        raise ValueError("Sequencer does not fit in Flash Page 0")

    args.output.mkdir(parents=True, exist_ok=False)

    (args.output / "sequencer.asm").write_text(SOURCE)
    (args.output / "sequencer.hex").write_text(text)
    (args.output / "build.json").write_text(
        json.dumps({
            "target": "Z8F0822",
            "board": "Zilog F082 Evaluation Board",
            "leds": {
                "red": "PA0",
                "green": "PA1",
                "yellow": "PA2",
            },
            "active": "low",
            "preserve_pa3_pa7": True,
            "hex_sha256": hashlib.sha256(
                text.encode("ascii")
            ).hexdigest(),
            "placed": placed,
            "symbols": symbols,
            "code_end_exclusive": end,
            "delay_timing_calibrated": False,
            "hardware_io": False,
            "hardware_execution_allowed": False,
        }, indent=2) + "\n"
    )

    print("Built:", args.output / "sequencer.hex")
    print("Code end:", hex(end))
    print("Hardware I/O: NONE")


if __name__ == "__main__":
    main()
