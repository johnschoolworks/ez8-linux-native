"""Integration test against Zilog's Z8F0822 golden image."""

from pathlib import Path

from ez8native.linker import Linker, Section, Symbol, Relocation


GOLDEN = (
    Path(__file__).parent
    / "golden/zilog/z8f0822/ledblink.hex"
)


def load_hex(path):
    memory = {}

    for line in path.read_text().splitlines():
        if not line:
            continue

        record = bytes.fromhex(line[1:])
        count = record[0]
        address = int.from_bytes(record[1:3], "big")
        kind = record[3]

        if kind == 0:
            for offset, value in enumerate(record[4:4 + count]):
                memory[address + offset] = value
        elif kind == 1:
            break
        else:
            raise ValueError(f"Unsupported HEX record: {kind}")

    return memory


def test_golden_section_layout_and_relocation():
    golden = load_hex(GOLDEN)

    linker = Linker({
        "ROM": (0x0000, 0x1FFF),
        "RDATA": (0x0020, 0x00DF),
    })

    # Reconstruct sections from actual Zilog golden bytes.
    linker.add_section(Section(
        "FLASH_OPTIONS",
        "ROM",
        bytes(golden[a] for a in range(0x0000, 0x0002)),
        address=0x0000,
    ))

    # Reset vector is resolved by the native linker.
    linker.add_section(Section(
        "RESET_VECTOR",
        "ROM",
        b"\x00\x00",
        address=0x0002,
    ))

    linker.add_section(Section(
        "INTERRUPT_VECTORS",
        "ROM",
        bytes(golden[a] for a in range(0x0006, 0x0038)),
        address=0x0006,
    ))

    linker.add_section(Section(
        "STARTUP",
        "ROM",
        bytes(golden[a] for a in range(0x0038, 0x0048)),
        address=0x0038,
    ))

    linker.add_section(Section(
        "CODE",
        "ROM",
        bytes(golden[a] for a in range(0x0048, 0x01E3)),
        address=0x0048,
    ))

    linker.add_section(Section(
        "ROM_TEXT",
        "ROM",
        bytes(golden[a] for a in range(0x01E3, 0x022C)),
        address=0x01E3,
    ))

    linker.add_section(Section(
        "NEAR_DATA",
        "RDATA",
        bytes(4),
        address=0x0020,
    ))

    linker.add_symbol(Symbol("reset", "STARTUP", 0))
    linker.add_relocation(Relocation(
        "RESET_VECTOR", 0, "reset", "ABS16_BE"
    ))

    placed, symbols, output = linker.link()

    assert symbols["reset"] == 0x0038
    assert output["RESET_VECTOR"] == b"\x00\x38"

    rebuilt = {}

    for name, data in output.items():
        if linker.sections[name].space != "ROM":
            continue

        for offset, value in enumerate(data):
            address = placed[name] + offset
            assert address not in rebuilt
            rebuilt[address] = value

    assert rebuilt == golden
    assert len(rebuilt) == 554
    assert max(rebuilt) == 0x022B
