"""Reproducible Z8F0822 startup parity against Zilog Golden HEX."""

from pathlib import Path

from ez8native.memory_map import RANGES
from ez8native.object_asm import assemble_object
from ez8native.object_link import link_objects


ROOT = Path(__file__).resolve().parents[1]

STARTUP_SOURCE = ROOT / "examples/z8f0822/startup.asm"
MAIN_SOURCE = ROOT / "examples/z8f0822/main.asm"
GOLDEN_HEX = ROOT / "tests/golden/zilog/z8f0822/ledblink.hex"

STARTUP_ADDRESS = 0x0038
MAIN_ADDRESS = 0x013E
STARTUP_SIZE = 16


def read_golden_rom(path):
    """Read Intel HEX into a sparse address map with integrity checks."""
    memory = {}
    base = 0
    eof = False

    for line_number, line in enumerate(
        path.read_text(encoding="ascii").splitlines(), 1
    ):
        line = line.strip()
        if not line:
            continue

        if not line.startswith(":"):
            raise ValueError(f"Line {line_number}: invalid HEX record")

        record = bytes.fromhex(line[1:])
        if len(record) < 5 or len(record) != record[0] + 5:
            raise ValueError(f"Line {line_number}: invalid record length")
        if sum(record) % 256:
            raise ValueError(f"Line {line_number}: checksum mismatch")

        count = record[0]
        address = int.from_bytes(record[1:3], "big")
        kind = record[3]
        data = record[4:4 + count]

        if kind == 0x00:
            for offset, value in enumerate(data):
                absolute = base + address + offset
                if absolute in memory:
                    raise ValueError(
                        f"Duplicate address: 0x{absolute:04X}"
                    )
                memory[absolute] = value

        elif kind == 0x01:
            if count != 0:
                raise ValueError("Invalid EOF record")
            eof = True
            break

        elif kind == 0x02:
            if count != 2:
                raise ValueError("Invalid segment address record")
            base = int.from_bytes(data, "big") << 4

        elif kind == 0x04:
            if count != 2:
                raise ValueError("Invalid linear address record")
            base = int.from_bytes(data, "big") << 16

        elif kind in (0x03, 0x05):
            continue

        else:
            raise ValueError(
                f"Unsupported Intel HEX record type: {kind}"
            )

    if not eof:
        raise ValueError("Missing Intel HEX EOF record")

    return memory


def test_z8f0822_golden_startup_parity():
    startup = assemble_object(
        STARTUP_SOURCE.read_text(encoding="utf-8"),
        section="STARTUP",
    )
    main = assemble_object(
        MAIN_SOURCE.read_text(encoding="utf-8"),
        section="CODE",
    )

    startup["sections"][0]["address"] = STARTUP_ADDRESS
    main["sections"][0]["address"] = MAIN_ADDRESS

    placed, symbols, output = link_objects(
        [startup, main], RANGES
    )

    golden = read_golden_rom(GOLDEN_HEX)

    expected = bytes(
        golden[address]
        for address in range(
            STARTUP_ADDRESS,
            STARTUP_ADDRESS + STARTUP_SIZE,
        )
    )

    actual = output["m0:STARTUP"]

    assert placed["m0:STARTUP"] == STARTUP_ADDRESS
    assert placed["m1:CODE"] == MAIN_ADDRESS
    assert len(actual) == STARTUP_SIZE
    assert actual == expected, (
        f"Golden: {expected.hex().upper()}\n"
        f"Native: {actual.hex().upper()}"
    )

    # Confirm the relocated CALL instruction points to MAIN.
    assert actual[11:14] == bytes([
        0xD6,
        MAIN_ADDRESS >> 8,
        MAIN_ADDRESS & 0xFF,
    ])

    # Confirm the startup termination loop.
    assert actual[14:16] == bytes([0x8B, 0xFE])
