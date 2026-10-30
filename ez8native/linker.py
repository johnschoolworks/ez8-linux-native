"""Native eZ8 linker: segment placement and relocation."""

from dataclasses import dataclass
from typing import Optional


class LinkError(Exception):
    pass


@dataclass
class Section:
    name: str
    space: str
    data: bytes
    alignment: int = 1
    address: Optional[int] = None


@dataclass
class Symbol:
    name: str
    section: str
    offset: int


@dataclass
class Relocation:
    section: str
    offset: int
    symbol: str
    kind: str
    addend: int = 0


class Linker:
    def __init__(self, ranges):
        self.ranges = dict(ranges)
        self.sections = {}
        self.symbols = {}
        self.relocations = []

    def add_section(self, section):
        if section.name in self.sections:
            raise LinkError(f"Duplicate section: {section.name}")
        if section.space not in self.ranges:
            raise LinkError(f"Unknown address space: {section.space}")
        if section.alignment <= 0:
            raise LinkError("Alignment must be positive")
        self.sections[section.name] = section

    def add_symbol(self, symbol):
        if symbol.name in self.symbols:
            raise LinkError(f"Duplicate symbol: {symbol.name}")
        self.symbols[symbol.name] = symbol

    def add_relocation(self, relocation):
        self.relocations.append(relocation)

    @staticmethod
    def align_up(value, alignment):
        return ((value + alignment - 1) // alignment) * alignment

    def link(self):
        placed = {}
        occupied = {
            space: set() for space in self.ranges
        }

        # Fixed sections must be reserved before automatic placement.
        ordered = sorted(
            self.sections.values(),
            key=lambda section: section.address is None,
        )

        for section in ordered:
            low, high = self.ranges[section.space]
            size = len(section.data)

            if section.address is not None:
                candidates = [section.address]
            else:
                candidates = range(
                    self.align_up(low, section.alignment),
                    high - size + 2,
                    section.alignment,
                )

            selected = None

            for address in candidates:
                if address % section.alignment:
                    continue

                if address < low or address + size > high + 1:
                    continue

                if any(
                    location in occupied[section.space]
                    for location in range(address, address + size)
                ):
                    continue

                selected = address
                break

            if selected is None:
                raise LinkError(
                    f"Cannot place section: {section.name}"
                )

            placed[section.name] = selected

            occupied[section.space].update(
                range(selected, selected + size)
            )

        resolved = {}

        for symbol in self.symbols.values():
            if symbol.section not in placed:
                raise LinkError(
                    f"Undefined section: {symbol.section}"
                )

            section = self.sections[symbol.section]

            if not 0 <= symbol.offset <= len(section.data):
                raise LinkError(
                    f"Invalid symbol offset: {symbol.name}"
                )

            resolved[symbol.name] = (
                placed[symbol.section] + symbol.offset
            )

        output = {
            name: bytearray(section.data)
            for name, section in self.sections.items()
        }

        for relocation in self.relocations:
            if relocation.section not in output:
                raise LinkError(
                    f"Unknown relocation section: "
                    f"{relocation.section}"
                )

            if relocation.symbol not in resolved:
                raise LinkError(
                    f"Undefined symbol: {relocation.symbol}"
                )

            section = output[relocation.section]
            offset = relocation.offset

            value = (
                resolved[relocation.symbol]
                + relocation.addend
            )

            if relocation.kind == "ABS16_BE":
                if not 0 <= offset <= len(section) - 2:
                    raise LinkError("ABS16 offset invalid")

                if not 0 <= value <= 0xFFFF:
                    raise LinkError("ABS16 overflow")

                section[offset:offset + 2] = (
                    value.to_bytes(2, "big")
                )

            elif relocation.kind == "ABS8":
                if not 0 <= offset < len(section):
                    raise LinkError("ABS8 offset invalid")

                if not 0 <= value <= 0xFF:
                    raise LinkError("ABS8 overflow")

                section[offset] = value

            elif relocation.kind == "REL8":
                if not 0 <= offset < len(section):
                    raise LinkError("REL8 offset invalid")

                pc_after = (
                    placed[relocation.section]
                    + offset + 1
                )

                displacement = value - pc_after

                if not -128 <= displacement <= 127:
                    raise LinkError("REL8 overflow")

                section[offset] = displacement & 0xFF

            else:
                raise LinkError(
                    f"Unsupported relocation: {relocation.kind}"
                )

        return (
            placed,
            resolved,
            {
                name: bytes(data)
                for name, data in output.items()
            },
        )
