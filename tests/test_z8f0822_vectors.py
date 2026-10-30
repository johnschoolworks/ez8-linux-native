import pytest

from ez8native.vectors import (
    VectorOwnershipError,
    validate_vector_ownership,
)


def test_owned_reset_vector():
    header = {0: 0, 1: 0, 2: 0, 3: 0x38}
    symbols = {"m0:RESET": 0x0038}
    manifest = {0x0002: "m0:RESET"}

    assert validate_vector_ownership(
        header, symbols, manifest
    )


def test_unowned_interrupt_rejected():
    header = {
        0: 0, 1: 0,
        2: 0, 3: 0x38,
        6: 0x01, 7: 0xE2,
    }
    symbols = {"m0:RESET": 0x0038}
    manifest = {0x0002: "m0:RESET"}

    with pytest.raises(
        VectorOwnershipError,
        match="unowned populated vector",
    ):
        validate_vector_ownership(header, symbols, manifest)


def test_wrong_reset_target_rejected():
    header = {0: 0, 1: 0, 2: 0, 3: 0x48}
    symbols = {"m0:RESET": 0x0038}
    manifest = {0x0002: "m0:RESET"}

    with pytest.raises(
        VectorOwnershipError,
        match="targets",
    ):
        validate_vector_ownership(header, symbols, manifest)


def test_undefined_vector_preserved():
    header = {0: 0, 1: 0, 2: 0, 3: 0x38}
    symbols = {"m0:RESET": 0x0038}
    manifest = {0x0002: "m0:RESET"}

    assert 0x0004 not in header
    assert 0x0005 not in header

    assert validate_vector_ownership(
        header, symbols, manifest
    )


def test_owner_outside_native_section_rejected():
    header = {0: 0, 1: 0, 2: 0, 3: 0x38}
    symbols = {"m0:RESET": 0x0038}

    with pytest.raises(
        VectorOwnershipError,
        match="owner not in native executable section",
    ):
        validate_vector_ownership(
            header,
            symbols,
            {0x0002: "m0:RESET"},
            executable_ranges=[(0x0048, 0x0050)],
        )


def test_owner_inside_native_section_accepted():
    header = {0: 0, 1: 0, 2: 0, 3: 0x38}
    symbols = {"m0:RESET": 0x0038}

    assert validate_vector_ownership(
        header,
        symbols,
        {0x0002: "m0:RESET"},
        executable_ranges=[(0x0038, 0x0048)],
    )
