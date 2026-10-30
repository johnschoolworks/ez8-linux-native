"""eZ8 register encoding matrix regression tests."""

import unittest

from ez8native.instructions import encode
from ez8native.asm import assemble


class RegisterMatrixTests(unittest.TestCase):

    def test_all_working_registers(self):
        for r in range(16):
            with self.subTest(register=r):
                self.assertEqual(
                    encode(f"INC R{r}"),
                    bytes([(r << 4) | 0x0E])
                )

                self.assertEqual(
                    encode(f"DEC R{r}"),
                    bytes([0x30, 0xE0 | r])
                )

                self.assertEqual(
                    encode(f"CLR R{r}"),
                    bytes([0xB0, 0xE0 | r])
                )

                self.assertEqual(
                    encode(f"LD R{r}, #055H"),
                    bytes([(r << 4) | 0x0C, 0x55])
                )

    def test_register_to_register(self):
        cases = {
            "LD R1, R0": "E4E0E1",
            "LD R3, R2": "E4E2E3",
            "LD R6, R4": "E4E4E6",
            "LD R15, R14": "E4EEEF",
        }

        for instruction, expected in cases.items():
            with self.subTest(instruction=instruction):
                self.assertEqual(
                    encode(instruction),
                    bytes.fromhex(expected)
                )

    def test_full_register_matrix(self):
        from pathlib import Path

        source = Path(
            "tests/golden/reference/register_matrix.asm"
        ).read_text()

        memory = assemble(source)

        self.assertEqual(len(memory), 124)
        self.assertEqual(memory[0], 0x0E)
        self.assertEqual(memory[0x79], 0xE4)


if __name__ == "__main__":
    unittest.main()
