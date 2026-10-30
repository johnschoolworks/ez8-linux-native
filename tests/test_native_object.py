import copy
import pytest
from ez8native.object import dumps_object, loads_object, ObjectFormatError
from ez8native.object_link import link_objects
from ez8native.linker import LinkError

RANGES = {'ROM': (0, 0x1fff)}

def module(name, data, address, symbols=(), relocations=()):
    return {'format': 'ezo', 'version': 1, 'cpu': 'Z8F0822',
            'sections': [{'name': name, 'space': 'ROM', 'data': data.hex(), 'alignment': 1, 'address': address}],
            'symbols': list(symbols), 'relocations': list(relocations)}

def sym(name, section, binding='global'):
    return {'name': name, 'section': section, 'offset': 0, 'binding': binding}

def rel(section, offset, symbol, kind):
    return {'section': section, 'offset': offset, 'symbol': symbol, 'kind': kind, 'addend': 0}

def test_roundtrip():
    obj = module('code', b'\xaf', 0x38, [sym('start', 'code')])
    assert loads_object(dumps_object(obj)) == obj

def test_cross_module_call_and_vector():
    start = module('vectors', b'\x00\x00\xd6\x00\x00', 2,
                   relocations=[rel('vectors', 0, 'entry', 'ABS16_BE'), rel('vectors', 3, 'entry', 'ABS16_BE')])
    main = module('main', b'\xaf', 0x38, [sym('entry', 'main')])
    placed, resolved, output = link_objects([start, main], RANGES)
    assert output['m0:vectors'] == bytes.fromhex('0038d60038')
    assert resolved['m1:entry'] == 0x38

def test_cross_module_jr():
    start = module('caller', b'\x8b\x00', 0x100, relocations=[rel('caller', 1, 'loop', 'REL8')])
    main = module('target', b'\xaf', 0x110, [sym('loop', 'target')])
    _, _, output = link_objects([start, main], RANGES)
    assert output['m0:caller'] == b'\x8b\x0e'

def test_local_symbols_do_not_collide():
    a = module('a', b'\xaf', 0x100, [sym('loop', 'a', 'local')])
    b = module('b', b'\xaf', 0x110, [sym('loop', 'b', 'local')])
    _, resolved, _ = link_objects([a, b], RANGES)
    assert resolved['m0:loop'] == 0x100
    assert resolved['m1:loop'] == 0x110

def test_duplicate_globals_rejected():
    a = module('a', b'\xaf', 0x100, [sym('entry', 'a')])
    b = module('b', b'\xaf', 0x110, [sym('entry', 'b')])
    with pytest.raises(LinkError, match='duplicate global'):
        link_objects([a, b], RANGES)

def test_undefined_external_rejected():
    a = module('a', b'\xd6\x00\x00', 0x100, relocations=[rel('a', 1, 'missing', 'ABS16_BE')])
    with pytest.raises(LinkError, match='undefined external'):
        link_objects([a], RANGES)

def test_invalid_relocation_bounds_rejected():
    a = module('a', b'\xaf', 0x100, relocations=[rel('a', 0, 'missing', 'ABS16_BE')])
    with pytest.raises(ObjectFormatError, match='out of bounds'):
        dumps_object(a)

def test_invalid_version_rejected():
    a = module('a', b'\xaf', 0x100)
    a['version'] = 2
    with pytest.raises(ObjectFormatError, match='version'):
        dumps_object(a)

def test_unsupported_cpu_rejected():
    a = module('a', b'\xaf', 0x100)
    a['cpu'] = 'unknown'
    with pytest.raises(ObjectFormatError, match='CPU'):
        dumps_object(a)

def test_duplicate_section_rejected():
    a = module('a', b'\xaf', 0x100)
    a['sections'].append(copy.deepcopy(a['sections'][0]))
    with pytest.raises(ObjectFormatError, match='duplicate'):
        dumps_object(a)
