import unittest
from ez8native.asm import assemble, intel_hex, AssemblyError

class AssemblerTests(unittest.TestCase):
    def test_bytes_and_org(self):
        self.assertEqual(assemble('.org 0x10\n.db 0x12, 34\n'), {16:18,17:34})
    def test_labels(self):
        self.assertEqual(assemble('start:\n.db start, end\nend:\n.db 3'), {0:0,1:2,2:3})
    def test_overlap_rejected(self):
        with self.assertRaises(AssemblyError):
            assemble('.db 1\n.org 0\n.db 2')
    def test_unknown_opcode_rejected(self):
        with self.assertRaises(AssemblyError):
            assemble('UNSUPPORTED_OPCODE')
    def test_hex_checksum(self):
        self.assertEqual(intel_hex({0:0x12,1:0x34}), ':020000001234B8\n:00000001FF\n')
    def test_sparse(self):
        self.assertEqual(len(intel_hex({0:1,32:2}).splitlines()),3)

if __name__ == '__main__':
    unittest.main()
