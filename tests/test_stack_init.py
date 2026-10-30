"""Golden-verified Z8F0822 stack initialization."""

import unittest
from pathlib import Path

from ez8native.asm import assemble


EXPECTED = bytes.fromhex(
    "8F 01 00 "
    "E9 FF 0F FF "
    "E9 00 0F FE "
    "D6 00 10 "
    "8B FE "
    "AF"
)


class StackInitializationTests(unittest.TestCase):

    def test_zilog_golden_reference(self):
        source = Path(
            "tests/golden/reference/stack_init_native.asm"
        ).read_text()

        memory = assemble(source)

        actual = bytes(
            memory[i] for i in range(len(EXPECTED))
        )

        self.assertEqual(len(memory), len(EXPECTED))
        self.assertEqual(actual, EXPECTED)


if __name__ == "__main__":
    unittest.main()
