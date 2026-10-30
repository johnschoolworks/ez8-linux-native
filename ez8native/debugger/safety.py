"""Default-deny safety boundary for the offline debugger prototype."""


class SafetyViolation(RuntimeError):
    """A request could affect real hardware or is outside the mock policy."""


def require_mock(transport: object) -> None:
    # Exact class check prevents a subclass from silently adding physical I/O.
    from .mock_transport import MockTransport

    if type(transport) is not MockTransport:
        raise SafetyViolation("V0.1 accepts only the exact MockTransport type")


def deny_target_operation(operation: str) -> None:
    raise SafetyViolation(f"Target operation prohibited: {operation}")
