; eZ8 Instruction Encoding Reference
; Target: Zilog Z8 Encore! / eZ8 CPU
; Purpose: Golden reference for native assembler development

    NOP
    INC R0
    DEC R0
    LD R0, #055H
    LD R1, R0
    CLR R0
    RET
