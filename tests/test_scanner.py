from pathlib import Path
import pytest

import klmr.pylox.scanner
from klmr.pylox.token import TokenType

from .log import MockLogger


def scan(source: str):
    return list(klmr.pylox.scanner.scan(source, MockLogger()))


# These test cases originally come from the original Lox repository
# <https://github.com/munificent/craftinginterpreters/tree/01e6f5b8f3e5dfa65674c2f9cf4700d73ab41cf8/test/scanning>
# The expected parses were modified to be valid Python expressions in the last
# column so that we can compare them here.
# Also rename some tokens; namely: EQUAL => EQ, GREATER => GT, LESS => LT.
def collect_test_cases():
    datadir = Path(__file__).parent / 'data/scan'
    return [(file, parse_expected(file)) for file in datadir.iterdir()]


def parse_expected(file: Path) -> list[list[str]]:
    def split_line(line: str):
        items = line.replace('// expect: ', '').strip().split(' ', 3)
        return [*items[0:2], eval(items[2])]

    with open(file, 'r') as f:
        return [
            split_line(line) for line in f
            if line.startswith('// expect:')
        ]


@pytest.mark.parametrize('file,expected', collect_test_cases())
def test_scanner_with_code(file: str, expected: str):
    with open(file, 'r') as f:
        contents = f.read()

    tokens = scan(contents)

    assert len(tokens) == len(expected)

    for token, exp in zip(tokens, expected):
        assert token.type == TokenType[exp[0]]
        assert token.lexeme == exp[1]
        if len(exp) == 3:
            assert token.literal == exp[2]


def test_fail_unterminated_string():
    with pytest.raises(ValueError, match='Unterminated string'):
        scan('"test')


def test_fail_unespected_char():
    with pytest.raises(ValueError, match='Unexpected character'):
        scan('1/?')
