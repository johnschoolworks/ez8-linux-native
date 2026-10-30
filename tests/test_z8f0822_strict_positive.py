import json
import subprocess
import sys
from pathlib import Path

from ez8native.object_asm import assemble_object
from ez8native.firmware import parse_golden_header_hex

ROOT = Path(__file__).resolve().parents[1]


def test_strict_positive_build(tmp_path):
    startup = assemble_object(
        (ROOT / "examples/z8f0822/startup.asm").read_text(),
        section="STARTUP",
    )
    main = assemble_object(
        (ROOT / "examples/z8f0822/main.asm").read_text(),
        section="CODE",
    )

    startup_path = tmp_path / "startup.ezo"
    main_path = tmp_path / "main.ezo"
    startup_path.write_text(json.dumps(startup))
    main_path.write_text(json.dumps(main))

    # Sparse header: option bytes + RESET vector only.
    # 0x0002..0x0003 will be replaced with native RESET address.
    header = tmp_path / "reset-only.hex"
    header.write_text(
        ":04000000FFFF0000FE\n"
        ":00000001FF\n"
    )

    output = tmp_path / "strict.hex"

    result = subprocess.run(
        [
            sys.executable, "-B", "-m", "ez8native.firmware",
            str(startup_path),
            str(main_path),
            "--vector-template", str(header),
            "--vector-manifest",
            str(ROOT / "examples/z8f0822/manifests/reset-only.json"),
            "-o", str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert output.exists()

    memory = parse_golden_header_hex(output.read_text())
    assert memory[0x0002] == 0x00
    assert memory[0x0003] == 0x38

    assert "strict vectors" in result.stdout


def test_strict_failure_preserves_existing_hex(tmp_path):
    startup = assemble_object(
        (ROOT / "examples/z8f0822/startup.asm").read_text(),
        section="STARTUP",
    )

    startup_path = tmp_path / "startup.ezo"
    startup_path.write_text(json.dumps(startup))

    header = tmp_path / "reset-only.hex"
    header.write_text(
        ":04000000FFFF0000FE\n"
        ":00000001FF\n"
    )

    bad_manifest = tmp_path / "bad-manifest.json"
    bad_manifest.write_text(json.dumps({
        "schema_version": 1,
        "device": "WRONG_DEVICE",
        "vectors": [],
    }))

    output = tmp_path / "existing.hex"
    output.write_text("DO_NOT_OVERWRITE\n")

    result = subprocess.run(
        [
            sys.executable, "-B", "-m", "ez8native.firmware",
            str(startup_path),
            "--vector-template", str(header),
            "--vector-manifest", str(bad_manifest),
            "-o", str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "incorrect target device" in result.stderr
    assert output.read_text() == "DO_NOT_OVERWRITE\n"
