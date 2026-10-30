"""Z8F0822 vector ownership validation.

This is a static validation gate, not hardware boot certification.
"""

from .memory_map import (
    HEADER_SIZE,
    RESET_VECTOR_ADDRESS,
    ROM_END,
)


class VectorOwnershipError(ValueError):
    pass


def validate_vector_ownership(header, symbols, manifest, *, executable_ranges=None):
    """Validate explicitly owned vectors against linked symbols.

    manifest maps vector byte addresses to fully qualified linker
    symbol names, e.g. {0x0002: "m0:RESET"}.

    Every populated non-reset vector must be explicitly owned.
    """

    if not isinstance(header, dict):
        raise VectorOwnershipError(
            "header must be a sparse address-to-byte mapping"
        )

    if not isinstance(manifest, dict):
        raise VectorOwnershipError("manifest must be a mapping")

    if RESET_VECTOR_ADDRESS not in manifest:
        raise VectorOwnershipError(
            "RESET vector must have an explicit owner"
        )

    for address, owner in manifest.items():
        if (
            not isinstance(address, int)
            or isinstance(address, bool)
            or address < RESET_VECTOR_ADDRESS
            or address + 1 >= HEADER_SIZE
            or address % 2
        ):
            raise VectorOwnershipError(
                f"invalid vector address: {address!r}"
            )

        if not isinstance(owner, str) or owner not in symbols:
            raise VectorOwnershipError(
                f"unresolved vector owner: {owner!r}"
            )

        target = symbols[owner]

        if not isinstance(target, int) or not 0x0038 <= target <= ROM_END:
            raise VectorOwnershipError(
                f"owner outside code ROM: {owner}"
            )

        if executable_ranges is not None:
            if not any(
                start <= target < end
                for start, end in executable_ranges
            ):
                raise VectorOwnershipError(
                    f"owner not in native executable section: {owner}"
                )

        if address not in header or address + 1 not in header:
            raise VectorOwnershipError(
                f"missing vector bytes at 0x{address:04X}"
            )

        encoded = (header[address] << 8) | header[address + 1]

        if encoded != target:
            raise VectorOwnershipError(
                f"vector 0x{address:04X} targets "
                f"0x{encoded:04X}, owner {owner} is 0x{target:04X}"
            )

    for address in range(RESET_VECTOR_ADDRESS, HEADER_SIZE, 2):
        present = address in header or address + 1 in header

        if present and address not in manifest:
            raise VectorOwnershipError(
                f"unowned populated vector at 0x{address:04X}"
            )

    return True
