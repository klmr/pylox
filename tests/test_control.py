from pathlib import Path
import pytest

import klmr.pylox


test_cases = ['fib1', 'dangling_else']
datadir = Path(__file__).parent / 'data'


@pytest.mark.parametrize("test_case", test_cases)
def test_control(test_case: str, capsys: pytest.CaptureFixture):
    with open(datadir / f'{test_case}.expected', 'r') as file:
        expected = file.read()

    klmr.pylox.run_script(datadir / f'{test_case}.lox')
    res = capsys.readouterr()
    assert res.err == ''
    assert res.out == expected
