import pytest
from pathlib import Path

from ez8native.firmware import (
    build_firmware,
    load_vector_template,
)
from ez8native.object_asm import assemble_object
from ez8native.vectors import VectorOwnershipError


ROOT = Path(__file__).resolve().parents[1]


def test_golden_header_rejected_by_ownership_gate():
    startup = assemble_object(
        (ROOT / "examples/z8f0822/startup.asm").read_text(),
        section="STARTUP",
    )
    main = assemble_object(
        (ROOT / "examples/z8f0822/main.asm").read_text(),
        section="CODE",
    )

    golden = load_vector_template(
        ROOT / "tests/golden/zilog/z8f0822/ledblink.hex"
    )

    with pytest.raises(
        VectorOwnershipError,
        match="unowned populated vector",
    ):
        build_firmware(
            [startup, main],
            golden,
            vector_manifest={0x0002: "m0:RESET"},
        )
