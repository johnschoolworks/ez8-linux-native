"""Golden-verified eZ8 startup instruction tests."""

import unittest
from pathlib import Path

from ez8native.asm import assemble
from ez8native.instructions import encode


EXPECTED = bytes.fromhex("8F 01 00 0F 8B FA")


class StartupTests(unittest.TestCase):

    def test_di(self):
        self.assertEqual(encode("DI"), bytes.fromhex("8F"))

    def test_srp_zero(self):
        self.assertEqual(
            encode("SRP #%00"),
            bytes.fromhex("01 00"),
        )

    def test_golden_reference(self):
        source = Path(
            "tests/golden/reference/startup.asm"
        ).read_text()

        memory = assemble(source)

        self.assertEqual(
            bytes(memory[i] for i in range(len(EXPECTED))),
            EXPECTED,
        )


if __name__ == "__main__":
    unittest.main()
