import tempfile
import os
"""Golden-header-based Z8F0822 firmware image assembly (experimental)."""
import argparse
from pathlib import Path

from .asm import intel_hex
from .linker import LinkError
from .memory_map import (HEADER_SIZE, RANGES, RESET_VECTOR_ADDRESS,
                         STARTUP_ADDRESS)
from .object import read_object
from .object_link import link_objects
from .vectors import validate_vector_ownership



def parse_golden_header_hex(text):
    """Read only explicit ROM bytes in the golden Intel HEX boot header."""
    memory = {}
    base = 0
    eof = False
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if eof:
            raise ValueError(f'HEX line {number}: data after EOF')
        if not line.startswith(':'):
            raise ValueError(f'HEX line {number}: missing colon')
        try:
            record = bytes.fromhex(line[1:])
        except ValueError as exc:
            raise ValueError(f'HEX line {number}: invalid hex') from exc
        if len(record) < 5 or len(record) != record[0] + 5:
            raise ValueError(f'HEX line {number}: invalid length')
        if sum(record) % 256:
            raise ValueError(f'HEX line {number}: checksum mismatch')
        count = record[0]
        offset = int.from_bytes(record[1:3], 'big')
        kind = record[3]
        data = record[4:-1]
        if kind == 0:
            if offset + count > 0x10000:
                raise ValueError(f'HEX line {number}: record crosses address boundary')
            for i, byte in enumerate(data):
                addr = base + offset + i
                if addr < HEADER_SIZE:
                    if addr in memory:
                        raise ValueError(f'HEX line {number}: duplicate header address 0x{addr:04X}')
                    memory[addr] = byte
        elif kind == 1:
            if count or offset:
                raise ValueError(f'HEX line {number}: malformed EOF')
            eof = True
        elif kind == 2:
            if count != 2 or offset:
                raise ValueError(f'HEX line {number}: malformed segment address')
            base = int.from_bytes(data, 'big') << 4
        elif kind == 4:
            if count != 2 or offset:
                raise ValueError(f'HEX line {number}: malformed linear address')
            base = int.from_bytes(data, 'big') << 16
        elif kind in (3, 5):
            if count != 4 or offset:
                raise ValueError(f'HEX line {number}: malformed start address')
        else:
            raise ValueError(f'HEX line {number}: unsupported record type {kind}')
    if not eof:
        raise ValueError('Golden HEX missing EOF')
    required = (0, 1, RESET_VECTOR_ADDRESS, RESET_VECTOR_ADDRESS + 1)
    missing = [a for a in required if a not in memory]
    if missing:
        raise ValueError(f'Golden HEX missing mandatory option/reset bytes: {missing}')
    return memory


def load_vector_template(path):
    """Accept sparse golden .hex or legacy contiguous 56-byte .bin."""
    path = Path(path)
    if path.suffix.lower() == '.hex':
        return parse_golden_header_hex(path.read_text(encoding='ascii'))
    return path.read_bytes()

def build_firmware(objects, vector_template, *, reset_symbol='RESET', vector_manifest=None):
    """Return (Intel HEX, placement, resolved symbols, non-ROM section data).

    The 56-byte template must be extracted/verified from the Zilog golden ROM.
    Its reset vector bytes are replaced with the native RESET symbol address.
    Non-ROM address spaces are linked but deliberately not emitted as ROM HEX.
    """
    if isinstance(vector_template, dict):
        if any(not isinstance(a, int) or not 0 <= a < HEADER_SIZE or
               not isinstance(b, int) or not 0 <= b <= 255
               for a, b in vector_template.items()):
            raise ValueError('invalid sparse vector template address or byte')
        if any(a not in vector_template for a in (0, 1, 2, 3)):
            raise ValueError('sparse vector template missing flash options/reset vector')
        header = dict(vector_template)
    else:
        if len(vector_template) != HEADER_SIZE:
            raise ValueError('vector template must be exactly 56 bytes (0x0000..0x0037)')
        header = dict(enumerate(vector_template))
    if not objects:
        raise ValueError('at least one EZO object is required')

    # Do not mutate callers' validated objects. STARTUP must be fixed at 0x0038.
    import copy
    modules = copy.deepcopy(objects)
    startup_sections = []
    for index, obj in enumerate(modules):
        for section in obj['sections']:
            if section['space'] == 'ROM' and section['name'] == 'STARTUP':
                startup_sections.append((index, section))
    if len(startup_sections) != 1:
        raise LinkError('exactly one ROM STARTUP section is required')
    startup_index, startup = startup_sections[0]
    if startup['address'] not in (None, STARTUP_ADDRESS):
        raise LinkError('STARTUP must be placed at 0x0038')
    startup['address'] = STARTUP_ADDRESS

    placed, symbols, output = link_objects(modules, RANGES)
    matches = [(name, address) for name, address in symbols.items()
               if name.endswith(':' + reset_symbol)]
    if len(matches) != 1:
        raise LinkError('exactly one RESET symbol is required')
    reset_name, reset_address = matches[0]
    if reset_name.split(':')[0] != f'm{startup_index}':
        raise LinkError('RESET symbol must belong to STARTUP module')
    reset_definitions = [s for s in modules[startup_index]['symbols']
                         if s['name'] == reset_symbol]
    if len(reset_definitions) != 1 or reset_definitions[0]['section'] != 'STARTUP':
        raise LinkError('RESET symbol must be defined inside STARTUP')
    if not STARTUP_ADDRESS <= reset_address <= 0x1FFF:
        raise LinkError('RESET address outside ROM')
    if reset_address >= STARTUP_ADDRESS + len(output[f'm{startup_index}:STARTUP']):
        raise LinkError('RESET must point inside STARTUP')

    rom = header
    rom[RESET_VECTOR_ADDRESS] = (reset_address >> 8) & 0xFF
    rom[RESET_VECTOR_ADDRESS + 1] = reset_address & 0xFF
    if vector_manifest is not None:
        executable_ranges = []
        for index, obj in enumerate(modules):
            for section in obj["sections"]:
                if section["space"] != "ROM":
                    continue
                key = f'm{index}:{section["name"]}'
                start = placed[key]
                size = len(output[key])
                if size:
                    executable_ranges.append(
                        (start, start + size)
                    )

        validate_vector_ownership(
            rom,
            symbols,
            vector_manifest,
            executable_ranges=executable_ranges,
        )
    non_rom = {}
    for index, obj in enumerate(modules):
        for section in obj['sections']:
            name = f'm{index}:{section["name"]}'
            if section['space'] != 'ROM':
                non_rom[name] = (section['space'], placed[name], output[name])
                continue
            for offset, byte in enumerate(output[name]):
                address = placed[name] + offset
                if address in rom:
                    raise LinkError(f'ROM overlap at 0x{address:04X}')
                rom[address] = byte
    return intel_hex(rom), placed, symbols, non_rom


def main(argv=None):
    from .vector_manifest import load_vector_manifest

    parser = argparse.ArgumentParser(
        description="Z8F0822 native firmware builder "
                    "(experimental unless vector manifest is supplied)"
    )
    parser.add_argument("objects", nargs="+", type=Path)
    parser.add_argument(
        "--vector-template",
        required=True,
        type=Path,
        help="56-byte ROM header template",
    )
    parser.add_argument(
        "--vector-manifest",
        type=Path,
        help="Enable strict vector ownership validation using JSON manifest",
    )
    parser.add_argument("-o", "--output", required=True, type=Path)

    args = parser.parse_args(argv)

    try:
        manifest = (
            load_vector_manifest(args.vector_manifest)
            if args.vector_manifest is not None
            else None
        )

        text, placed, symbols, non_rom = build_firmware(
            [read_object(p) for p in args.objects],
            load_vector_template(args.vector_template),
            vector_manifest=manifest,
        )

        # All validation must finish before output is written.
        args.output.parent.mkdir(parents=True, exist_ok=True)

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="ascii",
                dir=args.output.parent,
                prefix=f".{args.output.name}.",
                suffix=".tmp",
                delete=False,
            ) as temp:
                temp_path = Path(temp.name)
                temp.write(text)
                temp.flush()
                os.fsync(temp.fileno())

            os.replace(temp_path, args.output)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    except (ValueError, LinkError, OSError) as exc:
        parser.error(str(exc))

    for name, addr in placed.items():
        print(f"{name}: 0x{addr:04X}")

    for name, (space, addr, data) in non_rom.items():
        print(
            f"{name}: {space} 0x{addr:04X} "
            f"({len(data)} bytes, NOT in ROM HEX)"
        )

    mode = "strict vectors" if manifest is not None else "experimental"
    print(
        f"Wrote {args.output} "
        f"({mode}; hardware boot NOT verified)"
    )


if __name__ == '__main__':
    main()
