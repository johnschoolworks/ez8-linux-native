"""Zilog golden-verified GPIO instruction tests."""

import unittest
from pathlib import Path

from ez8native.asm import assemble, AssemblyError
from ez8native.instructions import encode, InstructionError


EXPECTED = bytes.fromhex(
    "E9 01 0F D0 "
    "E9 00 0F D1 "
    "E9 07 0F D3 "
    "59 FE 0F D3 "
    "49 07 0F D3 "
    "8B FE"
)


class GPIOTests(unittest.TestCase):

    def test_golden_reference(self):
        source = Path(
            "tests/golden/reference/gpio.asm"
        ).read_text()

        memory = assemble(source)
        self.assertEqual(
            bytes(memory[i] for i in range(22)),
            EXPECTED,
        )

    def test_ldx(self):
        self.assertEqual(
            encode("LDX 0xFD0, #0x01"),
            bytes.fromhex("E9 01 0F D0"),
        )

    def test_andx(self):
        self.assertEqual(
            encode("ANDX 0xFD3, #0xFE"),
            bytes.fromhex("59 FE 0F D3"),
        )

    def test_orx(self):
        self.assertEqual(
            encode("ORX 0xFD3, #0x07"),
            bytes.fromhex("49 07 0F D3"),
        )

    def test_duplicate_equ(self):
        with self.assertRaises(AssemblyError):
            assemble("VALUE EQU %01\nVALUE EQU %02")

    def test_undefined_symbol(self):
        with self.assertRaises(InstructionError):
            encode("LDX UNKNOWN, #0x01")

    def test_immediate_range(self):
        with self.assertRaises(InstructionError):
            encode("LDX 0xFD0, #0x100")


if __name__ == "__main__":
    unittest.main()
