"""Firmware layout tests: synthetic templates are NOT actual flash options."""
import copy
import pytest
from ez8native.firmware import build_firmware
from ez8native.linker import LinkError
from ez8native.memory_map import RANGES


def obj(name, data, symbols=(), space='ROM', address=None):
    return {'format':'ezo','version':1,'cpu':'Z8F0822',
            'sections':[{'name':name,'space':space,'data':data,'alignment':1,'address':address}],
            'symbols':list(symbols),'relocations':[]}


def startup():
    return obj('STARTUP','0faf', [{'name':'RESET','section':'STARTUP','offset':0,'binding':'global'}])


def parse_hex(text):
    result = {}
    for line in text.splitlines():
        record = bytes.fromhex(line[1:])
        assert sum(record) % 256 == 0
        size, addr, kind = record[0], int.from_bytes(record[1:3], 'big'), record[3]
        if kind == 0:
            for i, byte in enumerate(record[4:4+size]):
                result[addr+i] = byte
        elif kind == 1:
            assert size == 0
        else:
            pytest.fail(f'unexpected record type {kind}')
    return result


def test_memory_map_independent_spaces():
    assert RANGES['ROM'][0] == 0x38
    assert RANGES['RDATA'] == (0x20, 0xdf)


def test_reset_vector_and_header_preservation():
    header = bytes(range(56))  # synthetic fixture, NOT flashable
    firmware, placed, symbols, other = build_firmware([startup(), obj('CODE','0faf')], header)
    rom = parse_hex(firmware)
    assert placed == {'m0:STARTUP':0x38,'m1:CODE':0x3a}
    assert symbols['m0:RESET'] == 0x38
    assert bytes(rom[i] for i in range(56)) == header[:2] + b'\x00\x38' + header[4:]
    assert bytes(rom[i] for i in range(0x38,0x3c)) == bytes.fromhex('0faf0faf')
    assert not other


def test_template_size_rejected():
    with pytest.raises(ValueError, match='56 bytes'):
        build_firmware([startup()], b'\xff'*55)


def test_startup_required_once():
    with pytest.raises(LinkError, match='exactly one'):
        build_firmware([obj('CODE','0f')], b'\xff'*56)
    with pytest.raises(LinkError, match='exactly one'):
        build_firmware([startup(),startup()], b'\xff'*56)


def test_startup_fixed_address_enforced():
    with pytest.raises(LinkError, match='0x0038'):
        build_firmware([obj('STARTUP','0faf',startup()['symbols'],address=0x40)], b'\xff'*56)


def test_reset_symbol_required_and_inside_startup():
    with pytest.raises(LinkError, match='RESET'):
        build_firmware([obj('STARTUP','0faf')], b'\xff'*56)
    bad = startup()
    bad['symbols'][0]['offset'] = 2
    with pytest.raises(LinkError, match='inside STARTUP'):
        build_firmware([bad], b'\xff'*56)


def test_rdata_not_written_into_rom_hex():
    firmware, placed, _, other = build_firmware(
        [startup(),obj('NEAR_DATA','11223344',space='RDATA')], b'\xff'*56)
    rom = parse_hex(firmware)
    assert placed['m1:NEAR_DATA'] == 0x20
    assert other['m1:NEAR_DATA'] == ('RDATA',0x20,bytes.fromhex('11223344'))
    assert rom[0x20] == 0xff


def test_rom_fixed_section_in_header_rejected():
    with pytest.raises(LinkError, match='Cannot place section'):
        build_firmware([startup(),obj('BAD','0f',address=0x20)], b'\xff'*56)


def test_does_not_mutate_input():
    original = startup()
    snapshot = copy.deepcopy(original)
    build_firmware([original], b'\xff'*56)
    assert original == snapshot
