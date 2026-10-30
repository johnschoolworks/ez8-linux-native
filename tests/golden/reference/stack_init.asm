; Z8F0822 Stack Initialization Golden Reference
; Zilog eZ8 Macro Assembler 2.60

NEAR_STACK  EQU %00FF

start:
    DI
    SRP #%00
    LDX SPL, #%FF
    LDX SPH, #%00
    CALL main

exit:
    JR exit

main:
    RET
