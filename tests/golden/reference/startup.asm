; eZ8 Startup Opcode Golden Reference
; Target: Z8F0822
; Reference: Zilog eZ8 Macro Assembler 2.60

start:
    DI
    SRP #%00
    NOP
    JR start
