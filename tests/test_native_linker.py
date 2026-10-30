import pytest

from ez8native.linker import (
    Linker,
    LinkError,
    Section,
    Symbol,
    Relocation,
)


RANGES = {
    "ROM": (0x0000, 0x1FFF),
    "RDATA": (0x0020, 0x00DF),
}


def test_golden_segment_placement():
    linker = Linker(RANGES)

    linker.add_section(Section(
        "STARTUP", "ROM", bytes(16), address=0x0038
    ))
    linker.add_section(Section(
        "CODE", "ROM", bytes(411), address=0x0048
    ))
    linker.add_section(Section(
        "ROM_TEXT", "ROM", bytes(73), address=0x01E3
    ))

    placed, _, _ = linker.link()

    assert placed["STARTUP"] == 0x0038
    assert placed["CODE"] == 0x0048
    assert placed["ROM_TEXT"] == 0x01E3


def test_separate_address_spaces():
    linker = Linker(RANGES)

    linker.add_section(Section(
        "VECTOR", "ROM", b"\x00\x00", address=0x0020
    ))
    linker.add_section(Section(
        "NEAR_DATA", "RDATA", bytes(4), address=0x0020
    ))

    placed, _, _ = linker.link()

    assert placed["VECTOR"] == 0x0020
    assert placed["NEAR_DATA"] == 0x0020


def test_absolute_relocation():
    linker = Linker(RANGES)

    linker.add_section(Section(
        "VECTOR", "ROM", b"\x00\x00", address=0x0002
    ))
    linker.add_section(Section(
        "STARTUP", "ROM", b"\x8F", address=0x0038
    ))

    linker.add_symbol(Symbol("reset", "STARTUP", 0))
    linker.add_relocation(Relocation(
        "VECTOR", 0, "reset", "ABS16_BE"
    ))

    _, resolved, output = linker.link()

    assert resolved["reset"] == 0x0038
    assert output["VECTOR"] == b"\x00\x38"


def test_relative_relocation():
    linker = Linker(RANGES)

    linker.add_section(Section(
        "LOOP", "ROM", b"\x8B\x00", address=0x0100
    ))
    linker.add_symbol(Symbol("loop", "LOOP", 0))
    linker.add_relocation(Relocation(
        "LOOP", 1, "loop", "REL8"
    ))

    _, _, output = linker.link()

    assert output["LOOP"] == b"\x8B\xFE"


def test_overlap_rejected():
    linker = Linker(RANGES)

    linker.add_section(Section(
        "A", "ROM", bytes(4), address=0x0100
    ))
    linker.add_section(Section(
        "B", "ROM", bytes(4), address=0x0102
    ))

    with pytest.raises(LinkError):
        linker.link()


def test_undefined_symbol_rejected():
    linker = Linker(RANGES)

    linker.add_section(Section(
        "CODE", "ROM", b"\x00\x00"
    ))
    linker.add_relocation(Relocation(
        "CODE", 0, "missing", "ABS16_BE"
    ))

    with pytest.raises(LinkError):
        linker.link()


def test_relative_overflow_rejected():
    linker = Linker(RANGES)

    linker.add_section(Section(
        "A", "ROM", b"\x8B\x00", address=0x0100
    ))
    linker.add_section(Section(
        "B", "ROM", b"\xAF", address=0x0300
    ))

    linker.add_symbol(Symbol("far", "B", 0))
    linker.add_relocation(Relocation(
        "A", 1, "far", "REL8"
    ))

    with pytest.raises(LinkError):
        linker.link()


def test_cross_section_call_relocation():
    linker = Linker(RANGES)

    linker.add_section(Section(
        "CALLER", "ROM", b"\xD6\x00\x00", address=0x0100
    ))
    linker.add_section(Section(
        "CALLEE", "ROM", b"\xAF", address=0x0200
    ))

    linker.add_symbol(Symbol("target", "CALLEE", 0))
    linker.add_relocation(Relocation(
        "CALLER", 1, "target", "ABS16_BE"
    ))

    _, _, output = linker.link()

    assert output["CALLER"] == b"\xD6\x02\x00"


def test_cross_section_relative_jump():
    linker = Linker(RANGES)

    linker.add_section(Section(
        "CALLER", "ROM", b"\x8B\x00", address=0x0100
    ))
    linker.add_section(Section(
        "TARGET", "ROM", b"\xAF", address=0x0110
    ))

    linker.add_symbol(Symbol("target", "TARGET", 0))
    linker.add_relocation(Relocation(
        "CALLER", 1, "target", "REL8"
    ))

    _, _, output = linker.link()

    assert output["CALLER"] == b"\x8B\x0E"


def test_automatic_placement_alignment():
    linker = Linker(RANGES)

    linker.add_section(Section(
        "FIXED", "ROM", bytes(3), address=0x0000
    ))
    linker.add_section(Section(
        "ALIGNED", "ROM", bytes(4), alignment=8
    ))

    placed, _, _ = linker.link()

    assert placed["ALIGNED"] == 0x0008


def test_abs8_overflow_rejected():
    linker = Linker(RANGES)

    linker.add_section(Section(
        "CODE", "ROM", b"\x00", address=0x0100
    ))
    linker.add_section(Section(
        "TARGET", "ROM", b"\xAF", address=0x0200
    ))

    linker.add_symbol(Symbol("target", "TARGET", 0))
    linker.add_relocation(Relocation(
        "CODE", 0, "target", "ABS8"
    ))

    with pytest.raises(LinkError):
        linker.link()


def test_rom_exhaustion_rejected():
    linker = Linker({
        "ROM": (0x0000, 0x000F),
    })

    linker.add_section(Section(
        "TOO_LARGE", "ROM", bytes(17)
    ))

    with pytest.raises(LinkError):
        linker.link()


def test_automatic_placement_skips_fixed_section():
    linker = Linker({
        "ROM": (0x0000, 0x001F),
    })

    linker.add_section(Section(
        "RESERVED", "ROM", bytes(8), address=0x0008
    ))
    linker.add_section(Section(
        "AUTO", "ROM", bytes(12)
    ))

    placed, _, _ = linker.link()

    assert placed["RESERVED"] == 0x0008
    assert placed["AUTO"] == 0x0010
