"""Golden sparse boot vector regression tests."""
import pytest
from ez8native.asm import intel_hex
from ez8native.firmware import build_firmware, parse_golden_header_hex


def startup():
    return {'format':'ezo','version':1,'cpu':'Z8F0822',
            'sections':[{'name':'STARTUP','space':'ROM','data':'0faf','alignment':1,'address':None}],
            'symbols':[{'name':'RESET','section':'STARTUP','offset':0,'binding':'global'}],
            'relocations':[]}


def test_sparse_golden_header_preserved():
    header = {i: 0xff for i in range(0x38) if i not in (4, 5)}
    header[2], header[3] = 0, 0x38
    parsed = parse_golden_header_hex(intel_hex(header))
    assert 4 not in parsed and 5 not in parsed
    text, placed, _, _ = build_firmware([startup()], parsed)
    rom = parse_golden_header_hex(text)
    assert 4 not in rom and 5 not in rom
    assert rom[0] == 0xff and rom[1] == 0xff
    assert rom[2] == 0 and rom[3] == 0x38
    assert placed['m0:STARTUP'] == 0x38


def test_corrupted_checksum_rejected():
    with pytest.raises(ValueError, match='checksum'):
        parse_golden_header_hex(':04000000FFFF0038C7\n:00000001FF\n')


def test_missing_reset_rejected():
    with pytest.raises(ValueError, match='missing mandatory'):
        parse_golden_header_hex(intel_hex({0:255, 1:255}))


def test_duplicate_header_rejected():
    line = intel_hex({0:255, 1:255, 2:0, 3:56}).splitlines()[0]
    with pytest.raises(ValueError, match='duplicate'):
        parse_golden_header_hex(line+'\n'+line+'\n:00000001FF\n')
