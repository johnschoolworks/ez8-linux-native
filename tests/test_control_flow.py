"""eZ8 control flow golden reference tests."""

import unittest

from ez8native.asm import assemble
from ez8native.instructions import encode, InstructionError


class ControlFlowTests(unittest.TestCase):

    def test_golden_reference(self):
        source = """
            NOP
        loop:
            INC R0
            JR loop
            JP target
            NOP
        target:
            CALL subroutine
            JR target
        subroutine:
            RET
        """

        expected = bytes.fromhex(
            "0F 0E 8B FD 8D 00 08 0F D6 00 0D 8B FB AF"
        )

        memory = assemble(source)
        actual = bytes(memory[i] for i in range(len(expected)))

        self.assertEqual(actual, expected)

    def test_backward_relative_jump(self):
        self.assertEqual(
            encode("JR loop", {"loop": 1}, pc=2),
            bytes.fromhex("8BFD"),
        )

    def test_absolute_jump(self):
        self.assertEqual(
            encode("JP target", {"target": 0x1234}, pc=0),
            bytes.fromhex("8D1234"),
        )

    def test_call(self):
        self.assertEqual(
            encode("CALL target", {"target": 0x1234}, pc=0),
            bytes.fromhex("D61234"),
        )

    def test_relative_range(self):
        with self.assertRaises(InstructionError):
            encode("JR far", {"far": 0x1000}, pc=0)


if __name__ == "__main__":
    unittest.main()
