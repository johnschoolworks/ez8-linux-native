; eZ8 Control Flow Encoding Reference
; Target: Z8 Encore! / eZ8

    NOP

loop:
    INC R0
    JR loop

    JP target

    NOP

target:
    CALL subroutine
    JR target

subroutine:
    RET
