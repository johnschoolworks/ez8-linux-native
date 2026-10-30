"""Experimental single-section relocatable eZ8 assembler (.ezo v1)."""
import argparse
import re
from pathlib import Path

from .asm import AssemblyError, number
from .instructions import (InstructionError, encode, instruction_size,
                           parse_branch, BRANCH_OPCODES)
from .object import CPU, FORMAT, VERSION, validate_object, write_object

_NAME = re.compile(r'[A-Za-z_]\w*\Z')


def _symbol(token):
    return token.upper() if _NAME.fullmatch(token) else None


def _constant(token, constants):
    return number(token, constants)


def assemble_object(source, *, section='CODE', space='ROM', alignment=1):
    """Produce an EZO dict; .org and multiple sections are not supported."""
    if not _NAME.fullmatch(section):
        raise AssemblyError('Invalid section name')
    if space != 'ROM':
        raise AssemblyError('Object emission v0.1 supports ROM only')
    if type(alignment) is not int or alignment < 1:
        raise AssemblyError('Invalid alignment')

    entries = []
    constants = {}
    labels = {}
    exports = set()
    externs = set()
    pc = 0
    for lineno, raw in enumerate(source.splitlines(), 1):
        line = raw.split(';', 1)[0].strip()
        if not line:
            continue
        try:
            m = re.fullmatch(r'([A-Za-z_]\w*)\s+EQU\s+(.+)', line, re.I)
            if m:
                name = m.group(1).upper()
                if name in labels or name in constants:
                    raise AssemblyError(f'Duplicate symbol: {name}')
                constants[name] = _constant(m.group(2), constants)
                continue
            m = re.match(r'^([A-Za-z_]\w*):(?:\s*(.*))?$', line)
            if m:
                name = m.group(1).upper()
                if name in labels or name in constants:
                    raise AssemblyError(f'Duplicate label: {name}')
                labels[name] = pc
                line = (m.group(2) or '').strip()
                if not line:
                    continue
            m = re.fullmatch(r'\.(global|extern)\s+(.+)', line, re.I)
            if m:
                names = [x.strip().upper() for x in m.group(2).split(',')]
                if not all(_NAME.fullmatch(x) for x in names):
                    raise AssemblyError('Invalid symbol declaration')
                (exports if m.group(1).lower() == 'global' else externs).update(names)
                continue
            if re.match(r'\.org\b', line, re.I):
                raise AssemblyError('.org is not supported in relocatable objects')
            m = re.fullmatch(r'\.(db|dw)\s+(.+)', line, re.I)
            if m:
                kind = m.group(1).lower()
                args = [x.strip() for x in m.group(2).split(',')]
                if not all(args):
                    raise AssemblyError('Empty data operand')
                entries.append((lineno, pc, kind, args))
                pc += len(args) * (1 if kind == 'db' else 2)
            else:
                size = instruction_size(line)
                entries.append((lineno, pc, 'instruction', line))
                pc += size
        except (AssemblyError, InstructionError) as exc:
            raise AssemblyError(f'Line {lineno}: {exc}') from exc
    if pc > 0x10000:
        raise AssemblyError('Section exceeds 16-bit address space')
    if exports - labels.keys():
        raise AssemblyError(f'Undefined exported symbols: {sorted(exports - labels.keys())}')
    if externs & labels.keys():
        raise AssemblyError(f'External symbols defined locally: {sorted(externs & labels.keys())}')
    if externs & constants.keys() or exports & constants.keys():
        raise AssemblyError('EQU constants cannot be global or extern')

    data = bytearray()
    relocations = []
    for lineno, offset, kind, arg in entries:
        try:
            if kind == 'instruction':
                branch = parse_branch(arg)
                if branch:
                    mnemonic, condition, operand = branch
                    sym = _symbol(operand)
                    if sym and sym not in constants:
                        if sym not in labels and sym not in externs:
                            raise AssemblyError(f'Undeclared external symbol: {sym}')
                        if mnemonic == 'JR':
                            payload = bytes([BRANCH_OPCODES[condition], 0])
                            reloc_kind = 'REL8'
                        else:
                            payload = bytes([0x8D if mnemonic == 'JP' else 0xD6, 0, 0])
                            reloc_kind = 'ABS16_BE'
                        relocations.append(dict(section=section, offset=offset + 1,
                                                symbol=sym, kind=reloc_kind, addend=0))
                    elif mnemonic == 'JR':
                        # An absolute JR target cannot be encoded before placement.
                        raise AssemblyError('Absolute JR operand requires relocation-aware symbol')
                    else:
                        payload = encode(arg, labels=constants, pc=0)
                else:
                    payload = encode(arg, labels=constants, pc=offset)
            else:
                payload = bytearray()
                for token in arg:
                    sym = _symbol(token)
                    if sym and sym not in constants:
                        if kind == 'db':
                            raise AssemblyError('.db symbolic addresses are not supported in v0.1')
                        if sym not in labels and sym not in externs:
                            raise AssemblyError(f'Undeclared external symbol: {sym}')
                        relocations.append(dict(section=section, offset=offset + len(payload),
                                                symbol=sym, kind='ABS16_BE', addend=0))
                        payload.extend(b'\x00\x00')
                    else:
                        value = _constant(token, constants)
                        limit = 0xff if kind == 'db' else 0xffff
                        if not 0 <= value <= limit:
                            raise AssemblyError(f'{kind} value out of range: {value}')
                        payload.extend(value.to_bytes(1 if kind == 'db' else 2, 'big'))
            if len(data) != offset:
                raise AssemblyError('Internal section offset mismatch')
            data.extend(payload)
        except (AssemblyError, InstructionError) as exc:
            raise AssemblyError(f'Line {lineno}: {exc}') from exc

    obj = dict(format=FORMAT, version=VERSION, cpu=CPU,
               sections=[dict(name=section, space=space, data=data.hex(),
                              alignment=alignment, address=None)],
               symbols=[dict(name=name, section=section, offset=offset,
                             binding='global' if name in exports else 'local')
                        for name, offset in labels.items()],
               relocations=relocations)
    return validate_object(obj)


def main():
    parser = argparse.ArgumentParser(description='Experimental native eZ8 EZO object assembler')
    parser.add_argument('input', type=Path)
    parser.add_argument('-o', '--output', required=True, type=Path)
    parser.add_argument('--section', default='CODE')
    args = parser.parse_args()
    try:
        obj = assemble_object(args.input.read_text(encoding='utf-8'), section=args.section)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_object(args.output, obj)
    except (AssemblyError, OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f'Wrote {args.output} (EZO v1, experimental)')


if __name__ == '__main__':
    main()
