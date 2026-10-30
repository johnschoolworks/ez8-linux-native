"""Offline-only diagnostic entrypoint; never accepts a serial port."""
import argparse
from .mock_transport import MockTransport
from .session import MockSession


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline synthetic Smart Cable test only")
    parser.add_argument("--mock-identify", action="store_true")
    args = parser.parse_args(argv)
    if not args.mock_identify:
        parser.error("only --mock-identify is supported")
    session = MockSession(MockTransport([b"\x01\x02\x03\x55\x88\x11"]))
    try:
        session.connect()
        print("MOCK ONLY: candidate handshake accepted; no hardware verified")
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
