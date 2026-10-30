"""Linux-native eZ8 object linker CLI."""

import argparse
from pathlib import Path

from .asm import intel_hex
from .linker import LinkError
from .object import ObjectFormatError, read_object
from .object_link import link_objects


def address(value):
    return int(value, 0)


def link_to_hex(paths, ranges):
    objects = [read_object(path) for path in paths]
    placed, symbols, output = link_objects(objects, ranges)

    memory = {}

    for index, obj in enumerate(objects):
        for section in obj["sections"]:
            if section["space"] != "ROM":
                continue

            name = f"m{index}:{section['name']}"
            start = placed[name]

            for offset, byte in enumerate(output[name]):
                location = start + offset

                if location in memory:
                    raise LinkError(
                        f"Overlapping ROM address: 0x{location:04X}"
                    )

                memory[location] = byte

    return intel_hex(memory), placed, symbols


def main():
    parser = argparse.ArgumentParser(
        description="Experimental native eZ8 linker"
    )

    parser.add_argument(
        "objects",
        nargs="+",
        type=Path,
        help="Input .ezo objects",
    )

    parser.add_argument(
        "--rom-start",
        type=address,
        default=0x0000,
    )

    parser.add_argument(
        "--rom-end",
        type=address,
        default=0x1FFF,
    )

    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=Path,
    )

    args = parser.parse_args()

    if not 0 <= args.rom_start <= args.rom_end <= 0xFFFF:
        parser.error("Invalid ROM address range")

    try:
        hex_data, placed, symbols = link_to_hex(
            args.objects,
            {"ROM": (args.rom_start, args.rom_end)},
        )

        args.output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        args.output.write_text(
            hex_data,
            encoding="ascii",
        )

    except (
        LinkError,
        ObjectFormatError,
        OSError,
        ValueError,
    ) as exc:
        parser.error(str(exc))

    for name, location in placed.items():
        print(f"{name}: 0x{location:04X}")

    print(f"Wrote {args.output} (experimental)")


if __name__ == "__main__":
    main()
