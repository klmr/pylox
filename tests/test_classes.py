from pathlib import Path
import pytest

from klmr.pylox.parser import parse
from klmr.pylox.scanner import scan

from . import run_script_test, run_test
from .log import LoxSyntaxError, MockLogger


test_cases = [
    'breakfast', 'cream', 'bagel', 'not_method', 'jane', 'bill', 'bacon', 'egotist', 'cake', 'thing', 'init',
    'init-return'
]
datadir = Path(__file__).parent / 'data'


def parse_test(code: str):
    logger = MockLogger()

    try:
        return parse(scan(code, logger), logger)
    except:  # noqa: E722
        pytest.fail('code should parse successfully')


@pytest.mark.parametrize('test_case', test_cases)
def test_bindings(test_case: str, capsys: pytest.CaptureFixture):
    with open(datadir / f'{test_case}.expected', 'r') as file:
        expected = file.read()

    run_script_test(datadir / f'{test_case}.lox')
    res = capsys.readouterr()
    assert res.err == ''
    assert res.out == expected


def test_can_create_object():
    code = '''
    class Bagel {}
    Bagel();
    '''

    try:
        run_test(code)
    except:  # noqa: E722
        pytest.fail('code should not raise an error')


parse_tests = [
    'egg.scramble(3).with(cheddar);',
    'someObject.someProperty = value;'
    'breakfast.omelette.filling.meat = ham;'
]


@pytest.mark.parametrize('test_case', parse_tests)
def test_can_parse_get_expr(test_case: str):
    parse_test(test_case)


def test_invalid_top_level_return():
    code = 'print this;'

    with pytest.raises(LoxSyntaxError, match = 'Can’t use \'this\' outside of a class'):
        run_test(code)


def test_invalid_unbound_this():
    code = '''
    fun notAMethod() {
        print this;
    }
    '''

    with pytest.raises(LoxSyntaxError, match = 'Can’t use \'this\' outside of a class'):
        run_test(code)


def test_invalid_init_return():
    code = '''
    class Foo {
      init() {
        return "something else";
      }
    }
    '''

    with pytest.raises(LoxSyntaxError, match = 'Can’t return a value from an initializer'):
        run_test(code)
