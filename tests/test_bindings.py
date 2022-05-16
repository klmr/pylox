from pathlib import Path
import pytest

from tests.log import LoxParseError

from . import run_script_test, run_test


test_cases = ['scope1', 'scope2', 'scope-closure']
datadir = Path(__file__).parent / 'data'


@pytest.mark.parametrize('test_case', test_cases)
def test_bindings(test_case: str, capsys: pytest.CaptureFixture):
    with open(datadir / f'{test_case}.expected', 'r') as file:
        expected = file.read()

    run_script_test(datadir / f'{test_case}.lox')
    res = capsys.readouterr()
    assert res.err == ''
    assert res.out == expected


def test_init_cannot_self_reference():
    code = '''
    var a = "outer";
    {
        var a = a;
    }
    '''

    with pytest.raises(LoxParseError, match = 'Can’t read local variable in its own initializer'):
        run_test(code)


def test_local_redefinition_error():
    code = '''
    fun bad() {
        var a = "first";
        var a = "second";
    }
    '''

    with pytest.raises(LoxParseError, match = 'Already a variable with this name in scope'):
        run_test(code)


def test_top_level_return_error():
    code = '''
    return "at top level";
    '''

    with pytest.raises(LoxParseError, match = 'at return: Can’t return from top-level code'):
        run_test(code)
