; Z8F0822 Native Startup
; Golden Startup Machine Code Parity

SPL EQU %0FFF
SPH EQU %0FFE

.global RESET
.extern MAIN

RESET:
    DI
    SRP #%00
    LDX SPL, #%FF
    LDX SPH, #%00
    CALL MAIN

EXIT:
    JR EXIT
