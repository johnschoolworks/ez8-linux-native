import pytest
from ez8native.asm import AssemblyError
from ez8native.object_asm import assemble_object
from ez8native.object_link import link_objects

RANGES = {'ROM': (0, 0x1fff)}


def test_call_across_objects():
    startup = assemble_object('.global reset\n.extern main\nreset:\n CALL main\n RET', section='STARTUP')
    main = assemble_object('.global main\nmain:\n NOP\n RET', section='CODE')
    placed, symbols, output = link_objects([startup, main], RANGES)
    assert placed == {'m0:STARTUP': 0, 'm1:CODE': 4}
    assert output['m0:STARTUP'] == b'\xd6\x00\x04\xaf'
    assert output['m1:CODE'] == b'\x0f\xaf'
    assert symbols['m1:MAIN'] == 4


def test_relative_cross_object():
    a = assemble_object('.extern target\n JR target', section='A')
    b = assemble_object('.global target\ntarget:\n RET', section='B')
    _, _, output = link_objects([a, b], RANGES)
    assert output['m0:A'] == b'\x8b\x00'


def test_local_jump_relocated():
    a = assemble_object('start: JR start', section='A')
    _, _, output = link_objects([a], {'ROM': (0x100, 0x1ff)})
    assert output['m0:A'] == b'\x8b\xfe'


def test_dw_external():
    a = assemble_object('.extern target\n.dw target', section='A')
    b = assemble_object('.global target\ntarget: RET', section='B')
    _, _, output = link_objects([a, b], RANGES)
    assert output['m0:A'] == b'\x00\x02'


@pytest.mark.parametrize('source', [
    '.org 0x100\nNOP', 'CALL missing', '.global missing\nNOP',
    '.extern foo\nfoo: RET', '.db missing', 'JR 0x100',
])
def test_rejected_inputs(source):
    with pytest.raises(AssemblyError):
        assemble_object(source)


def test_legacy_assembler_unchanged():
    from ez8native.asm import assemble
    assert assemble('NOP\nRET') == {0: 0x0f, 1: 0xaf}
