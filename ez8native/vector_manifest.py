"""Versioned Z8F0822 vector manifest loader."""

import json
from pathlib import Path

from .memory_map import RESET_VECTOR_ADDRESS
from .vectors import VectorOwnershipError


def load_vector_manifest(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise VectorOwnershipError("manifest must be an object")

    if data.get("schema_version") != 1:
        raise VectorOwnershipError("unsupported manifest version")

    if data.get("device") != "Z8F0822":
        raise VectorOwnershipError("incorrect target device")

    entries = data.get("vectors")

    if not isinstance(entries, list):
        raise VectorOwnershipError("vectors must be a list")

    owners = {}

    for entry in entries:
        if not isinstance(entry, dict):
            raise VectorOwnershipError("invalid vector entry")

        address_text = entry.get("address")
        symbol = entry.get("symbol")
        kind = entry.get("kind")

        if not isinstance(address_text, str):
            raise VectorOwnershipError("invalid vector address")

        try:
            address = int(address_text, 0)
        except ValueError as exc:
            raise VectorOwnershipError(
                "invalid vector address"
            ) from exc

        if not isinstance(symbol, str) or not symbol:
            raise VectorOwnershipError("invalid owner symbol")

        if kind not in ("reset", "interrupt"):
            raise VectorOwnershipError("invalid handler kind")

        if address == RESET_VECTOR_ADDRESS:
            if kind != "reset":
                raise VectorOwnershipError(
                    "reset vector requires reset handler"
                )
        elif kind != "interrupt":
            raise VectorOwnershipError(
                "non-reset vector requires interrupt handler"
            )

        if address in owners:
            raise VectorOwnershipError(
                f"duplicate vector: 0x{address:04X}"
            )

        owners[address] = symbol

    if RESET_VECTOR_ADDRESS not in owners:
        raise VectorOwnershipError("missing reset vector")

    return owners
