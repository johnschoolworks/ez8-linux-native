"""Versioned, validated eZ8 relocatable object format (.ezo)."""
from dataclasses import dataclass
import json
from pathlib import Path

FORMAT = 'ezo'
VERSION = 1
CPU = 'Z8F0822'
KINDS = {'ABS16_BE': 2, 'ABS8': 1, 'REL8': 1}

class ObjectFormatError(ValueError):
    pass


def _integer(value, what, minimum=0):
    if type(value) is not int or value < minimum:
        raise ObjectFormatError(f'{what} must be an integer >= {minimum}')
    return value


def _fields(value, keys, what):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ObjectFormatError(f'{what}: expected fields {sorted(keys)}')


def validate_object(obj):
    _fields(obj, ('format', 'version', 'cpu', 'sections', 'symbols', 'relocations'), 'object')
    if obj['format'] != FORMAT or type(obj['version']) is not int or obj['version'] != VERSION:
        raise ObjectFormatError('unsupported object format/version')
    if obj['cpu'] != CPU:
        raise ObjectFormatError('unsupported CPU')
    for key in ('sections', 'symbols', 'relocations'):
        if not isinstance(obj[key], list):
            raise ObjectFormatError(f'{key} must be an array')
    sections = {}
    for s in obj['sections']:
        _fields(s, ('name', 'space', 'data', 'alignment', 'address'), 'section')
        if not isinstance(s['name'], str) or not s['name'] or s['name'] in sections:
            raise ObjectFormatError('duplicate or invalid section name')
        if s['space'] not in ('ROM', 'RDATA', 'EDATA', 'PRAM', 'PAGE_E'):
            raise ObjectFormatError('unsupported address space')
        if not isinstance(s['data'], str) or len(s['data']) % 2:
            raise ObjectFormatError('section data must be even-length hex')
        try:
            raw = bytes.fromhex(s['data'])
        except ValueError as exc:
            raise ObjectFormatError('invalid section hex') from exc
        _integer(s['alignment'], 'alignment', 1)
        if s['address'] is not None:
            _integer(s['address'], 'address')
        sections[s['name']] = len(raw)
    symbols = set()
    for sym in obj['symbols']:
        _fields(sym, ('name', 'section', 'offset', 'binding'), 'symbol')
        if not isinstance(sym['name'], str) or not sym['name'] or sym['name'] in symbols:
            raise ObjectFormatError('duplicate or invalid symbol name')
        if sym['section'] not in sections:
            raise ObjectFormatError('symbol references unknown section')
        _integer(sym['offset'], 'symbol offset')
        if sym['offset'] > sections[sym['section']]:
            raise ObjectFormatError('symbol offset out of bounds')
        if sym['binding'] not in ('local', 'global'):
            raise ObjectFormatError('invalid symbol binding')
        symbols.add(sym['name'])
    for rel in obj['relocations']:
        _fields(rel, ('section', 'offset', 'symbol', 'kind', 'addend'), 'relocation')
        if rel['section'] not in sections:
            raise ObjectFormatError('relocation references unknown section')
        if not isinstance(rel['symbol'], str) or not rel['symbol']:
            raise ObjectFormatError('invalid relocation symbol')
        if rel['kind'] not in KINDS:
            raise ObjectFormatError('invalid relocation kind')
        _integer(rel['offset'], 'relocation offset')
        if rel['offset'] + KINDS[rel['kind']] > sections[rel['section']]:
            raise ObjectFormatError('relocation offset out of bounds')
        if type(rel['addend']) is not int:
            raise ObjectFormatError('addend must be integer')
    return obj


def dumps_object(obj):
    validate_object(obj)
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True) + '\n'


def loads_object(text):
    try:
        obj = json.loads(text)
    except (ValueError, TypeError) as exc:
        raise ObjectFormatError('invalid JSON object') from exc
    return validate_object(obj)


def read_object(path):
    return loads_object(Path(path).read_text(encoding='utf-8'))


def write_object(path, obj):
    Path(path).write_text(dumps_object(obj), encoding='utf-8')
