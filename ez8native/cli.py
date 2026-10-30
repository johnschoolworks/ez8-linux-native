"""Unified Linux-native eZ8 command-line interface.

G4.0: offline toolchain commands only.
Physical hardware operations are not exposed.
"""

import argparse
import runpy
import sys


COMMANDS = {
    "asm": "ez8native.asm",
    "object": "ez8native.object_asm",
    "link": "ez8native.link",
    "firmware": "ez8native.firmware",
    "debug-mock": "ez8native.debugger.cli",
}


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="ez8",
        description="Linux-native eZ8 toolchain (experimental)",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=COMMANDS,
        help="Toolchain command",
    )

    arguments = list(sys.argv[1:] if argv is None else argv)

    if not arguments or arguments == ["--help"] or arguments == ["-h"]:
        parser.print_help()
        return 0

    command, *remaining = arguments

    if command not in COMMANDS:
        parser.error(f"unknown command: {command}")

    module = COMMANDS[command]
    previous_argv = sys.argv[:]

    try:
        sys.argv = [module, *remaining]
        runpy.run_module(module, run_name="__main__")
    finally:
        sys.argv = previous_argv

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
