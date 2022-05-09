from pathlib import Path
import pytest

from . import run_script_test


def test_scope(capsys: pytest.CaptureFixture):
    datadir = Path(__file__).parent / 'data'
    script = datadir / 'scope.lox'
    with open(datadir / 'scope.expected', 'r') as file:
        expected = file.read()

    run_script_test(script)
    res = capsys.readouterr()
    assert res.err == ''
    assert res.out == expected
