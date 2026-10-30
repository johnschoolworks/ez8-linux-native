"""Golden-verified eZ8 conditional branch tests."""

import unittest
from pathlib import Path

from ez8native.asm import assemble
from ez8native.instructions import (
    encode,
    instruction_size,
    InstructionError,
)


class ConditionalBranchTests(unittest.TestCase):

    def test_golden_reference(self):
        source = Path(
            "tests/golden/reference/conditional_branch.asm"
        ).read_text()

        expected = bytes.fromhex(
            "B0 E0 "
            "6B 06 "
            "EB 07 "
            "7B 09 "
            "FB F6 "
            "0E "
            "8B F3 "
            "30 E0 "
            "8B F9 "
            "0F AF"
        )

        memory = assemble(source)
        actual = bytes(memory[i] for i in range(len(expected)))

        self.assertEqual(actual, expected)

    def test_conditional_opcodes(self):
        cases = {
            "JR Z, target": "6B00",
            "JR NZ, target": "EB00",
            "JR C, target": "7B00",
            "JR NC, target": "FB00",
        }

        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(
                    encode(source, {"target": 2}, pc=0),
                    bytes.fromhex(expected),
                )

    def test_instruction_sizes(self):
        self.assertEqual(instruction_size("JR Z, target"), 2)
        self.assertEqual(instruction_size("JR target"), 2)
        self.assertEqual(instruction_size("JP target"), 3)
        self.assertEqual(instruction_size("CALL target"), 3)
        self.assertEqual(instruction_size("INC R15"), 1)

    def test_out_of_range_branch(self):
        with self.assertRaises(InstructionError):
            encode("JR NZ, far", {"far": 0x1000}, pc=0)

    def test_undefined_label(self):
        with self.assertRaises(InstructionError):
            encode("JR Z, missing", {}, pc=0)


if __name__ == "__main__":
    unittest.main()
