"""Hardware Identify session.

The session does not open ports or perform target operations.
The caller supplies an already-open Transport.
"""

from .transport import Transport
from .cable_protocol import encode_identify
from .hardware_identify import parse_hardware_identify


class HardwareIdentifySession:
    def __init__(self, transport: Transport):
        if not isinstance(transport, Transport):
            raise TypeError("Expected Transport")
        self.transport = transport

    def identify(self) -> bytes:
        """Return the opaque three-byte suffix of the cable response."""
        self.transport.write_all(encode_identify())
        frame = self.transport.read_exact(6)
        return parse_hardware_identify(frame)
