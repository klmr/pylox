from pathlib import Path
import pytest

from klmr.pylox.log import LoxRuntimeError

from . import run_script_test, run_test


test_cases = ['fib1', 'dangling_else', 'count', 'add3', 'add2', 'hi', 'procedure', 'count-return', 'fib2', 'counter']
datadir = Path(__file__).parent / 'data'


@pytest.mark.parametrize("test_case", test_cases)
def test_control(test_case: str, capsys: pytest.CaptureFixture):
    with open(datadir / f'{test_case}.expected', 'r') as file:
        expected = file.read()

    run_script_test(datadir / f'{test_case}.lox')
    res = capsys.readouterr()
    assert res.err == ''
    assert res.out == expected


def test_can_only_call_fun():
    with pytest.raises(LoxRuntimeError, match = 'Can only call functions and classes'):
        run_test('"totally not a function"();')


def test_arity():
    fun = '''
    fun add(a, b, c) {
        print a + b + c;
    }
    '''

    with pytest.raises(LoxRuntimeError, match = 'Expected 3 arguments but got 4'):
        run_test(fun + 'add(1, 2, 3, 4);')

    with pytest.raises(LoxRuntimeError, match = 'Expected 3 arguments but got 2'):
        run_test(fun + 'add(1, 2);')
