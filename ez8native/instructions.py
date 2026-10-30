"""Native eZ8 instruction encoder.

Register encoding formulas validated against Zilog eZ8 Macro
Assembler 2.60 register matrix.
"""

import re


class InstructionError(ValueError):
    """Invalid or unsupported instruction."""


def parse_register(token):
    match = re.fullmatch(r"R(\d+)", token.strip().upper())

    if not match:
        raise InstructionError(f"Invalid register: {token}")

    register = int(match.group(1))

    if not 0 <= register <= 15:
        raise InstructionError(f"Register out of range: {token}")

    return register


def parse_immediate(token):
    token = token.strip().upper()

    if not token.startswith("#"):
        raise InstructionError("Immediate operand must start with #")

    value = token[1:]

    if re.fullmatch(r"0X[0-9A-F]+", value):
        number = int(value, 16)
    elif re.fullmatch(r"[0-9A-F]+H", value):
        number = int(value[:-1], 16)
    elif re.fullmatch(r"\d+", value):
        number = int(value, 10)
    else:
        raise InstructionError(f"Invalid immediate: {token}")

    if not 0 <= number <= 255:
        raise InstructionError("Immediate out of range")

    return number


EXTENDED_IMMEDIATE_OPCODES = {
    "LDX": 0xE9,
    "ANDX": 0x59,
    "ORX": 0x49,
}


def parse_extended(source):
    return re.fullmatch(
        r"(LDX|ANDX|ORX)\s+"
        r"([A-Z_]\w*|0X[0-9A-F]+|%[0-9A-F]+)\s*,\s*"
        r"#(0X[0-9A-F]+|[0-9A-F]+H|%[0-9A-F]+|\d+)",
        source.strip().upper(),
    )


def extended_number(token, symbols):
    token = token.upper()
    if token in symbols:
        return symbols[token]
    if token.startswith("%"):
        return int(token[1:], 16)
    if token.startswith("0X"):
        return int(token, 16)
    if token.endswith("H"):
        return int(token[:-1], 16)
    if token.isdecimal():
        return int(token, 10)
    raise InstructionError(f"Unknown extended operand: {token}")


BRANCH_OPCODES = {
    "": 0x8B,
    "Z": 0x6B,
    "NZ": 0xEB,
    "C": 0x7B,
    "NC": 0xFB,
}


def parse_branch(source):
    """Parse verified JR, JP and CALL instruction forms."""
    source = source.strip().upper()

    match = re.fullmatch(
        r"JR\s+(?:(Z|NZ|C|NC)\s*,\s*)?([A-Z_]\w*|0X[0-9A-F]+)",
        source,
    )
    if match:
        return ("JR", match.group(1) or "", match.group(2))

    match = re.fullmatch(
        r"(JP|CALL)\s+([A-Z_]\w*|0X[0-9A-F]+)",
        source,
    )
    if match:
        return (match.group(1), "", match.group(2))

    return None


def instruction_size(source):
    """Determine instruction size without resolving forward labels."""
    if parse_extended(source):
        return 4

    branch = parse_branch(source)

    if branch:
        return 2 if branch[0] == "JR" else 3

    return len(encode(source))


def encode(source, labels=None, pc=0):
    """Encode supported eZ8 instructions."""
    source = source.strip().upper()
    labels = {} if labels is None else labels

    extended = parse_extended(source)
    if extended:
        mnemonic, address_token, immediate_token = extended.groups()
        symbols = {
            name.upper(): value for name, value in labels.items()
        }
        address = extended_number(address_token, symbols)
        immediate = extended_number(immediate_token, symbols)

        if not 0 <= address <= 0xFFFF:
            raise InstructionError("Extended address out of range")
        if not 0 <= immediate <= 0xFF:
            raise InstructionError("Extended immediate out of range")

        return bytes([
            EXTENDED_IMMEDIATE_OPCODES[mnemonic],
            immediate,
            (address >> 8) & 0xFF,
            address & 0xFF,
        ])

    branch = parse_branch(source)

    if branch:
        mnemonic, condition, operand = branch

        if operand.startswith("0X"):
            target = int(operand, 16)
        else:
            symbols = {
                name.upper(): value
                for name, value in labels.items()
            }
            if operand not in symbols:
                raise InstructionError(f"Undefined label: {operand}")
            target = symbols[operand]

        if not 0 <= target <= 0xFFFF:
            raise InstructionError("Target address out of range")

        if mnemonic == "JR":
            displacement = target - (pc + 2)

            if not -128 <= displacement <= 127:
                raise InstructionError("JR displacement out of range")

            return bytes([
                BRANCH_OPCODES[condition],
                displacement & 0xFF,
            ])

        opcode = 0x8D if mnemonic == "JP" else 0xD6

        return bytes([
            opcode,
            target >> 8,
            target & 0xFF,
        ])

    if source == "DI":
        return bytes([0x8F])

    if source == "SRP #%00":
        return bytes([0x01, 0x00])

    if source == "NOP":
        return bytes([0x0F])

    if source == "RET":
        return bytes([0xAF])

    match = re.fullmatch(r"INC\s+(R\d+)", source)
    if match:
        register = parse_register(match.group(1))
        return bytes([(register << 4) | 0x0E])

    match = re.fullmatch(r"DEC\s+(R\d+)", source)
    if match:
        register = parse_register(match.group(1))
        return bytes([0x30, 0xE0 | register])

    match = re.fullmatch(r"CLR\s+(R\d+)", source)
    if match:
        register = parse_register(match.group(1))
        return bytes([0xB0, 0xE0 | register])

    match = re.fullmatch(r"LD\s+(R\d+)\s*,\s*(#[^\s,]+)", source)
    if match:
        register = parse_register(match.group(1))
        immediate = parse_immediate(match.group(2))
        return bytes([(register << 4) | 0x0C, immediate])

    match = re.fullmatch(r"LD\s+(R\d+)\s*,\s*(R\d+)", source)
    if match:
        destination = parse_register(match.group(1))
        source_register = parse_register(match.group(2))
        return bytes([
            0xE4,
            0xE0 | source_register,
            0xE0 | destination,
        ])

    raise InstructionError(f"Unsupported eZ8 instruction: {source}")
