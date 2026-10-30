from pathlib import Path

GOLDEN = (
    Path(__file__).parent
    / "golden/zilog/z8f0822/ledblink.hex"
)

ROM_SIZE = 0x2000
STARTUP = bytes.fromhex(
    "8F 01 00 E9 FF 0F FF E9 00 0F FE"
)


def load_intel_hex(path):
    memory = {}
    base = 0
    eof_seen = False

    for line_number, raw in enumerate(
        path.read_text().splitlines(), 1
    ):
        line = raw.strip()

        if not line:
            continue

        assert not eof_seen, (
            f"Data after EOF at line {line_number}"
        )
        assert line.startswith(":"), (
            f"Invalid HEX record at line {line_number}"
        )

        record = bytes.fromhex(line[1:])
        assert len(record) >= 5

        count = record[0]
        assert len(record) == count + 5
        assert sum(record) % 256 == 0, (
            f"Checksum failure at line {line_number}"
        )

        address = (record[1] << 8) | record[2]
        record_type = record[3]
        data = record[4:-1]

        if record_type == 0x00:
            for offset, value in enumerate(data):
                absolute = base + address + offset
                assert absolute < ROM_SIZE, (
                    f"ROM overflow: 0x{absolute:04X}"
                )
                assert absolute not in memory, (
                    f"Overlapping HEX data: 0x{absolute:04X}"
                )
                memory[absolute] = value

        elif record_type == 0x01:
            assert count == 0 and address == 0
            eof_seen = True

        elif record_type == 0x02:
            assert count == 2 and address == 0
            base = int.from_bytes(data, "big") << 4

        elif record_type == 0x04:
            assert count == 2 and address == 0
            base = int.from_bytes(data, "big") << 16

        else:
            raise AssertionError(
                f"Unsupported record type: {record_type}"
            )

    assert eof_seen, "Missing Intel HEX EOF"
    return memory


def test_golden_hex_integrity():
    memory = load_intel_hex(GOLDEN)

    assert memory
    assert max(memory) < ROM_SIZE


def test_flash_options():
    memory = load_intel_hex(GOLDEN)

    assert memory[0x0000] == 0xFF
    assert memory[0x0001] == 0xFF


def test_reset_vector():
    memory = load_intel_hex(GOLDEN)

    reset = (
        (memory[0x0002] << 8)
        | memory[0x0003]
    )

    assert reset == 0x0038


def test_startup_bytes():
    memory = load_intel_hex(GOLDEN)

    actual = bytes(
        memory[0x0038 + offset]
        for offset in range(len(STARTUP))
    )

    assert actual == STARTUP


def test_rom_usage():
    memory = load_intel_hex(GOLDEN)

    assert len(memory) == 554
    assert max(memory) == 0x022B
