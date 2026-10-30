; eZ8 GPIO Extended Addressing Golden Reference
; Target: Z8F0822
; Reference: Zilog ZDS II Macro Assembler

PAADDR  EQU %FD0
PACTL   EQU %FD1
PAOUT   EQU %FD3

start:
    LDX PAADDR, #%01
    LDX PACTL, #%00
    LDX PAOUT, #%07

    ANDX PAOUT, #%FE
    ORX PAOUT, #%07

loop:
    JR loop
