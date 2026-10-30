"""Golden instruction encoding regression tests."""

import unittest

from ez8native.asm import assemble
from ez8native.instructions import encode, InstructionError


class InstructionTests(unittest.TestCase):

    def test_golden_reference(self):
        source = """
            NOP
            INC R0
            DEC R0
            LD R0, #055H
            LD R1, R0
            CLR R0
            RET
        """

        expected = bytes.fromhex(
            "0F 0E 30 E0 0C 55 E4 E0 E1 B0 E0 AF"
        )

        memory = assemble(source)

        actual = bytes(memory[i] for i in range(len(expected)))
        self.assertEqual(actual, expected)

    def test_nop(self):
        self.assertEqual(encode("NOP"), b"\x0f")

    def test_ret(self):
        self.assertEqual(encode("RET"), b"\xaf")

    def test_immediate(self):
        self.assertEqual(encode("LD R0, #055H"), b"\x0c\x55")

    def test_unsupported_register(self):
        with self.assertRaises(InstructionError):
            encode("INC R16")

    def test_invalid_immediate(self):
        with self.assertRaises(InstructionError):
            encode("LD R0, #0x100")

    def test_instruction_label_address(self):
        memory = assemble("""
start:
    NOP
next:
    .dw next
""")
        self.assertEqual(memory, {0: 0x0F, 1: 0x00, 2: 0x01})


if __name__ == "__main__":
    unittest.main()
