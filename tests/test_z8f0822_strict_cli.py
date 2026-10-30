"""G2.4: Strict firmware CLI integration tests."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_firmware_cli(*args):
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    return subprocess.run(
        [sys.executable, "-B", "-m", "ez8native.firmware", *map(str, args)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=15,
    )


def test_cli_exposes_vector_manifest_option():
    result = run_firmware_cli("--help")

    assert result.returncode == 0
    assert "--vector-manifest" in result.stdout


def test_strict_cli_rejects_unowned_golden_vectors(tmp_path):
    from ez8native.object_asm import assemble_object
    import json

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

    output = tmp_path / "strict.hex"

    result = run_firmware_cli(
        startup_path,
        main_path,
        "--vector-template",
        ROOT / "tests/golden/zilog/z8f0822/ledblink.hex",
        "--vector-manifest",
        ROOT / "examples/z8f0822/manifests/reset-only.json",
        "-o",
        output,
    )

    assert result.returncode != 0
    assert "unowned populated vector" in (
        result.stdout + result.stderr
    )
    assert not output.exists()


def test_strict_cli_rejects_invalid_manifest(tmp_path):
    from ez8native.object_asm import assemble_object
    import json

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

    invalid_manifest = tmp_path / "invalid.json"
    invalid_manifest.write_text(
        json.dumps({
            "schema_version": 1,
            "device": "WRONG_DEVICE",
            "vectors": [],
        })
    )

    output = tmp_path / "invalid.hex"

    result = run_firmware_cli(
        startup_path,
        main_path,
        "--vector-template",
        ROOT / "tests/golden/zilog/z8f0822/ledblink.hex",
        "--vector-manifest",
        invalid_manifest,
        "-o",
        output,
    )

    assert result.returncode != 0
    assert "incorrect target device" in (
        result.stdout + result.stderr
    )
    assert not output.exists()
