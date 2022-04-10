from pathlib import Path
import pytest

import klmr.pylox


def test_scope(capsys: pytest.CaptureFixture):
    datadir = Path(__file__).parent / 'data'
    script = datadir / 'scope.lox'
    with open(datadir / 'scope.expected', 'r') as file:
        expected = file.read()

    klmr.pylox.run_script(script)
    res = capsys.readouterr()
    assert res.err == ''
    assert res.out == expected
