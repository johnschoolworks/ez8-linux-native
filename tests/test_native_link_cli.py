"""Native eZ8 linker CLI integration and failure tests."""

from pathlib import Path
import subprocess
import sys

import pytest

from ez8native.asm import intel_hex
from ez8native.object import write_object
from ez8native.link import link_to_hex


def make_object(
    name="CODE",
    data="0faf",
    address=None,
    symbols=None,
    relocations=None,
):
    return {
        "format": "ezo",
        "version": 1,
        "cpu": "Z8F0822",
        "sections": [{
            "name": name,
            "space": "ROM",
            "data": data,
            "alignment": 1,
            "address": address,
        }],
        "symbols": symbols or [],
        "relocations": relocations or [],
    }


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-B", "-m", "ez8native.link", *map(str, args)],
        capture_output=True,
        text=True,
    )


def test_cli_cross_object_call(tmp_path):
    startup = make_object(
        name="STARTUP",
        data="d60000af",
        relocations=[{
            "section": "STARTUP",
            "offset": 1,
            "symbol": "MAIN",
            "kind": "ABS16_BE",
            "addend": 0,
        }],
    )
    main = make_object(
        symbols=[{
            "name": "MAIN",
            "section": "CODE",
            "offset": 0,
            "binding": "global",
        }],
    )

    first = tmp_path / "startup.ezo"
    second = tmp_path / "main.ezo"
    output = tmp_path / "firmware.hex"

    write_object(first, startup)
    write_object(second, main)

    result = run_cli(
        first, second,
        "--rom-start", "0x0038",
        "--rom-end", "0x1FFF",
        "-o", output,
    )

    assert result.returncode == 0, result.stderr
    assert output.read_text() == intel_hex({
        0x0038: 0xD6,
        0x0039: 0x00,
        0x003A: 0x3C,
        0x003B: 0xAF,
        0x003C: 0x0F,
        0x003D: 0xAF,
    })


def test_cli_rom_overflow(tmp_path):
    obj = tmp_path / "large.ezo"
    write_object(obj, make_object(data="00" * 17))

    result = run_cli(
        obj,
        "--rom-start", "0x0000",
        "--rom-end", "0x000F",
        "-o", tmp_path / "out.hex",
    )

    assert result.returncode != 0
    assert "Cannot place section" in result.stderr


def test_cli_undefined_external(tmp_path):
    obj = tmp_path / "missing.ezo"
    write_object(obj, make_object(
        data="d60000",
        relocations=[{
            "section": "CODE",
            "offset": 1,
            "symbol": "MISSING",
            "kind": "ABS16_BE",
            "addend": 0,
        }],
    ))

    result = run_cli(obj, "-o", tmp_path / "out.hex")

    assert result.returncode != 0
    assert "undefined external symbol" in result.stderr


def test_cli_invalid_rom_range(tmp_path):
    result = run_cli(
        tmp_path / "missing.ezo",
        "--rom-start", "0x2000",
        "--rom-end", "0x1FFF",
        "-o", tmp_path / "out.hex",
    )

    assert result.returncode != 0
    assert "Invalid ROM address range" in result.stderr


def test_cli_invalid_object(tmp_path):
    obj = tmp_path / "bad.ezo"
    obj.write_text('{"format": "invalid"}')

    result = run_cli(obj, "-o", tmp_path / "out.hex")

    assert result.returncode != 0
    assert "expected fields" in result.stderr


def test_cli_sparse_rom(tmp_path):
    first = tmp_path / "first.ezo"
    second = tmp_path / "second.ezo"

    write_object(first, make_object(
        name="FIRST",
        data="0f",
        address=0x0038,
    ))
    write_object(second, make_object(
        name="SECOND",
        data="af",
        address=0x0100,
    ))

    text, placed, _ = link_to_hex(
        [first, second],
        {"ROM": (0x0000, 0x1FFF)},
    )

    assert placed["m0:FIRST"] == 0x0038
    assert placed["m1:SECOND"] == 0x0100

    assert text == intel_hex({
        0x0038: 0x0F,
        0x0100: 0xAF,
    })


def test_cli_overlapping_sections(tmp_path):
    first = tmp_path / "first.ezo"
    second = tmp_path / "second.ezo"

    write_object(first, make_object(
        name="FIRST",
        data="0000",
        address=0x0038,
    ))
    write_object(second, make_object(
        name="SECOND",
        data="0000",
        address=0x0039,
    ))

    result = run_cli(
        first, second,
        "-o", tmp_path / "out.hex",
    )

    assert result.returncode != 0
    assert "Cannot place section" in result.stderr


def test_cli_hex_checksum(tmp_path):
    obj = tmp_path / "code.ezo"
    output = tmp_path / "code.hex"

    write_object(obj, make_object(data="0faf"))

    result = run_cli(obj, "-o", output)

    assert result.returncode == 0, result.stderr

    lines = output.read_text().splitlines()

    assert lines[-1] == ":00000001FF"

    for line in lines:
        assert line.startswith(":")
        record = bytes.fromhex(line[1:])
        assert len(record) == record[0] + 5
        assert sum(record) % 256 == 0


def test_cli_duplicate_global_symbol(tmp_path):
    symbol = [{
        "name": "MAIN",
        "section": "CODE",
        "offset": 0,
        "binding": "global",
    }]

    first = tmp_path / "first.ezo"
    second = tmp_path / "second.ezo"

    write_object(first, make_object(symbols=symbol))
    write_object(second, make_object(symbols=symbol))

    result = run_cli(
        first, second,
        "-o", tmp_path / "out.hex",
    )

    assert result.returncode != 0
    assert "duplicate global symbol" in result.stderr
