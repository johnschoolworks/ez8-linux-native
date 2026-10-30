"""Combine .ezo modules using the native Linker core."""
from .linker import Linker, Section, Symbol, Relocation, LinkError
from .object import validate_object, ObjectFormatError


def link_objects(objects, ranges):
    linker = Linker(ranges)
    globals_by_name = {}
    modules = []
    for index, obj in enumerate(objects):
        validate_object(obj)
        prefix = f'm{index}:'
        local_symbols = {}
        for s in obj['sections']:
            linker.add_section(Section(prefix + s['name'], s['space'], bytes.fromhex(s['data']), s['alignment'], s['address']))
        for sym in obj['symbols']:
            internal = prefix + sym['name']
            linker.add_symbol(Symbol(internal, prefix + sym['section'], sym['offset']))
            local_symbols[sym['name']] = internal
            if sym['binding'] == 'global':
                if sym['name'] in globals_by_name:
                    raise LinkError(f'duplicate global symbol: {sym["name"]}')
                globals_by_name[sym['name']] = internal
        modules.append((prefix, obj, local_symbols))
    for prefix, obj, local_symbols in modules:
        for rel in obj['relocations']:
            target = local_symbols.get(rel['symbol'], globals_by_name.get(rel['symbol']))
            if target is None:
                raise LinkError(f'undefined external symbol: {rel["symbol"]}')
            linker.add_relocation(Relocation(prefix + rel['section'], rel['offset'], target, rel['kind'], rel['addend']))
    return linker.link()
