from .instructions import instruction_size
"""Two-pass native eZ8 assembler with initial instruction support."""
import argparse
import ast
import re
from pathlib import Path
from ez8native.instructions import encode, InstructionError

class AssemblyError(ValueError):
    pass

def number(token, labels):
    token = token.strip()
    if token in labels:
        return labels[token]
    if token.upper() in labels:
        return labels[token.upper()]
    try:
        if token.startswith('%'):
            return int(token[1:], 16)
        if token.lower().startswith('0x'):
            return int(token, 16)
        if token.lower().endswith('h') and re.fullmatch(r'[0-9a-fA-F]+[hH]', token):
            return int(token[:-1], 16)
        if re.fullmatch(r'\d+', token):
            return int(token)
    except ValueError:
        pass
    raise AssemblyError(f'Unknown expression: {token}')

def parse(text):
    entries = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.split(';', 1)[0].strip()
        if not line:
            continue
        equ = re.fullmatch(
            r'([A-Za-z_]\w*)\s+EQU\s+(.+)', line, re.I
        )
        if equ:
            entries.append((lineno, 'equ', equ.groups()))
            continue
        m = re.match(r'^([A-Za-z_]\w*):(?:\s*(.*))?$', line)
        if m:
            entries.append((lineno, 'label', m.group(1)))
            line = (m.group(2) or '').strip()
            if not line:
                continue
        m = re.match(r'^\.(org|db|dw)\s+(.+)$', line, re.I)
        if not m:
            try:
                instruction_size(line)
            except InstructionError as exc:
                raise AssemblyError(f'Line {lineno}: {exc}') from exc
            entries.append((lineno, 'instruction', line))
            continue
        entries.append((lineno, m.group(1).lower(), [x.strip() for x in m.group(2).split(',')]))
    return entries

def assemble(text):
    entries = parse(text)
    labels = {}
    pc = 0
    for lineno, kind, arg in entries:
        if kind == 'equ':
            name, expression = arg
            name = name.upper()
            if name in labels:
                raise AssemblyError(
                    f'Line {lineno}: duplicate symbol {name}'
                )
            labels[name] = number(expression, labels)
            continue
        if kind == 'label':
            if arg in labels:
                raise AssemblyError(f'Line {lineno}: duplicate label {arg}')
            labels[arg] = pc
        elif kind == 'org':
            if len(arg) != 1:
                raise AssemblyError(f'Line {lineno}: .org takes one argument')
            pc = number(arg[0], labels)
        elif kind == 'instruction':
            pc += instruction_size(arg)
        else:
            pc += len(arg) * (1 if kind == 'db' else 2)
    memory = {}
    pc = 0
    for lineno, kind, arg in entries:
        if kind in ('label', 'equ'):
            continue
        if kind == 'org':
            pc = number(arg[0], labels)
            if not 0 <= pc <= 0xffff:
                raise AssemblyError(f'Line {lineno}: address outside 16-bit space')
            continue
        if kind == 'instruction':
            for byte in encode(arg, labels=labels, pc=pc):
                if pc in memory or pc > 0xffff:
                    raise AssemblyError(
                        f'Line {lineno}: overlapping/out-of-range address {pc:#x}'
                    )
                memory[pc] = byte
                pc += 1
            continue
        for token in arg:
            value = number(token, labels)
            limit = 255 if kind == 'db' else 65535
            if not 0 <= value <= limit:
                raise AssemblyError(f'Line {lineno}: {kind} value out of range: {value}')
            # .dw uses big-endian as a project-defined DATA convention,
            # NOT a verified eZ8 instruction or vector encoding.
            payload = [value] if kind == 'db' else [value >> 8, value & 255]
            for byte in payload:
                if pc in memory or pc > 0xffff:
                    raise AssemblyError(f'Line {lineno}: overlapping/out-of-range address {pc:#x}')
                memory[pc] = byte
                pc += 1
    return memory

def record(address, kind, payload):
    data = bytes([len(payload), address >> 8, address & 255, kind]) + bytes(payload)
    checksum = (-sum(data)) & 255
    return ':' + (data + bytes([checksum])).hex().upper()

def intel_hex(memory):
    if not memory:
        return record(0, 1, []) + '\n'
    addresses = sorted(memory)
    output = []
    start = addresses[0]
    chunk = [memory[start]]
    last = start
    for address in addresses[1:]:
        if address == last + 1 and len(chunk) < 16:
            chunk.append(memory[address])
        else:
            output.append(record(start, 0, chunk))
            start, chunk = address, [memory[address]]
        last = address
    output.append(record(start, 0, chunk))
    output.append(record(0, 1, []))
    return '\n'.join(output) + '\n'

def main():
    parser = argparse.ArgumentParser(description='Experimental native eZ8 assembler')
    parser.add_argument('input', type=Path)
    parser.add_argument('-o', '--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        data = assemble(args.input.read_text())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(intel_hex(data))
    except (AssemblyError, OSError) as exc:
        parser.error(str(exc))
    print(f'Wrote {args.output} ({len(data)} bytes; experimental, not flash-ready)')

if __name__ == '__main__':
    main()
