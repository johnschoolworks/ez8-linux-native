; eZ8 Conditional Branch Golden Reference

start:
    CLR R0
    JR Z, zero_path
    JR NZ, nonzero_path
    JR C, carry_path
    JR NC, start

zero_path:
    INC R0
    JR start

nonzero_path:
    DEC R0
    JR zero_path

carry_path:
    NOP
    RET
