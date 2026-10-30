"""G4.0 unified CLI offline regression tests."""

import hashlib
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "examples/z8f0822"
EXPECTED_SHA = (
    "90f1867a54c22b6e02cfa780af9bb8218e27b8ec5981820a7f00046ff0bdcb03"
)


def cli(*args):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(
        [sys.executable, "-B", "-m", "ez8native.cli", *map(str, args)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_top_level_help():
    result = cli("--help")
    assert result.returncode == 0
    assert "firmware" in result.stdout
    assert "debug-mock" in result.stdout


def test_object_help():
    result = cli("object", "--help")
    assert result.returncode == 0
    assert "--section" in result.stdout


def test_firmware_help():
    result = cli("firmware", "--help")
    assert result.returncode == 0
    assert "--vector-manifest" in result.stdout


def test_unknown_command_rejected():
    result = cli("flash")
    assert result.returncode != 0
    assert "unknown command" in result.stderr.lower()


def test_g39_firmware_reproducibility(tmp_path):
    baseline_dir = tmp_path / "g39-baseline"
    env = dict(
        os.environ,
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONPATH=str(ROOT),
    )
    result = subprocess.run(
        [sys.executable, "-B", str(SOURCE / "build_sequencer.py"),
         "--output", str(baseline_dir)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    baseline = baseline_dir / "sequencer.hex"
    assert baseline.is_file()
    assert hashlib.sha256(baseline.read_bytes()).hexdigest() == EXPECTED_SHA

    startup = tmp_path / "startup.ezo"
    sequencer = tmp_path / "sequencer.ezo"
    firmware = tmp_path / "sequencer.hex"

    commands = [
        (
            "object", SOURCE / "startup.asm",
            "--section", "STARTUP", "-o", startup,
        ),
        (
            "object", baseline_dir / "sequencer.asm",
            "--section", "CODE", "-o", sequencer,
        ),
        (
            "firmware", startup, sequencer,
            "--vector-template", SOURCE / "reset-only.hex",
            "--vector-manifest",
            SOURCE / "manifests/reset-only.json",
            "-o", firmware,
        ),
    ]

    for command in commands:
        result = cli(*command)
        assert result.returncode == 0, result.stdout + result.stderr

    assert firmware.read_bytes() == baseline.read_bytes()
    assert hashlib.sha256(firmware.read_bytes()).hexdigest() == EXPECTED_SHA
