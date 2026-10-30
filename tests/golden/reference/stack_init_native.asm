; Native eZ8 Stack Initialization Golden Reference
; Expected to match Zilog Macro Assembler 2.60

SPL_ADDR EQU %0FFF
SPH_ADDR EQU %0FFE
NEAR_STACK EQU %00FF

start:
    DI
    SRP #%00
    LDX SPL_ADDR, #%FF
    LDX SPH_ADDR, #%00
    CALL main

exit:
    JR exit

main:
    RET
