from pathlib import Path
import pytest

from . import run_test, run_script_test


def test_scope(capsys: pytest.CaptureFixture):
    datadir = Path(__file__).parent / 'data'
    script = datadir / 'scope.lox'
    with open(datadir / 'scope.expected', 'r') as file:
        expected = file.read()

    run_script_test(script)
    res = capsys.readouterr()
    assert res.err == ''
    assert res.out == expected


def test_scope_shadow(capsys: pytest.CaptureFixture):
    script = '''
    var a = 1;
    {
        var a = a + 1;
        print a;
    }
    print a;
    '''
    run_test(script)
    res = capsys.readouterr()
    assert res.err == ''
    assert res.out == '2\n1\n'
