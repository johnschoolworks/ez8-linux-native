import json

import pytest

from ez8native.vector_manifest import load_vector_manifest
from ez8native.vectors import VectorOwnershipError


def write_manifest(tmp_path, vectors, **overrides):
    data = {
        "schema_version": 1,
        "device": "Z8F0822",
        "vectors": vectors,
    }
    data.update(overrides)

    path = tmp_path / "vectors.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


RESET = {
    "address": "0x0002",
    "symbol": "m0:RESET",
    "kind": "reset",
}


def test_valid_reset_manifest(tmp_path):
    path = write_manifest(tmp_path, [RESET])
    assert load_vector_manifest(path) == {
        0x0002: "m0:RESET"
    }


def test_wrong_device_rejected(tmp_path):
    path = write_manifest(
        tmp_path, [RESET], device="Z8F1234"
    )
    with pytest.raises(
        VectorOwnershipError,
        match="incorrect target device",
    ):
        load_vector_manifest(path)


def test_duplicate_vector_rejected(tmp_path):
    path = write_manifest(tmp_path, [RESET, RESET])
    with pytest.raises(
        VectorOwnershipError,
        match="duplicate vector",
    ):
        load_vector_manifest(path)


def test_wrong_reset_kind_rejected(tmp_path):
    entry = dict(RESET, kind="interrupt")
    path = write_manifest(tmp_path, [entry])
    with pytest.raises(
        VectorOwnershipError,
        match="requires reset handler",
    ):
        load_vector_manifest(path)


def test_missing_reset_rejected(tmp_path):
    path = write_manifest(tmp_path, [])
    with pytest.raises(
        VectorOwnershipError,
        match="missing reset vector",
    ):
        load_vector_manifest(path)


def test_invalid_vector_address_rejected(tmp_path):
    entry = dict(RESET, address="not-hex")
    path = write_manifest(tmp_path, [entry])
    with pytest.raises(
        VectorOwnershipError,
        match="invalid vector address",
    ):
        load_vector_manifest(path)
