from typing import Iterable, Optional, Tuple

from .log import Logger, position_from_offset
from .token import Token, TokenType as T


def scan(source: str, logger: Logger) -> Iterable[Token]:
    return Scanner(source, logger).tokens()


_KEYWORD_TOKENS = {
    'and': T.AND,
    'class': T.CLASS,
    'else': T.ELSE,
    'false': T.FALSE,
    'for': T.FOR,
    'fun': T.FUN,
    'if': T.IF,
    'nil': T.NIL,
    'or': T.OR,
    'print': T.PRINT,
    'return': T.RETURN,
    'super': T.SUPER,
    'this': T.THIS,
    'true': T.TRUE,
    'var': T.VAR,
    'while': T.WHILE
}


class Scanner:
    def __init__(self, source: str, logger: Logger) -> None:
        self._source = source
        self._logger = logger
        self._start = 0
        self._pos = 0

    def tokens(self) -> Iterable[Token]:
        while not self._at_end():
            self._start = self._pos
            token = self._scan_token()
            if token:
                yield token
        yield Token(T.EOF, '', None, self._pos, 0)

    def _scan_token(self) -> Optional[Token]:
        c = self._advance()
        if c == '(':
            return self._token(T.LEFT_PAREN)
        elif c == ')':
            return self._token(T.RIGHT_PAREN)
        elif c == '{':
            return self._token(T.LEFT_BRACE)
        elif c == '}':
            return self._token(T.RIGHT_BRACE)
        elif c == ',':
            return self._token(T.COMMA)
        elif c == '.':
            return self._token(T.DOT)
        elif c == '-':
            return self._token(T.MINUS)
        elif c == '+':
            return self._token(T.PLUS)
        elif c == ';':
            return self._token(T.SEMICOLON)
        elif c == '*':
            return self._token(T.STAR)
        elif c == '!':
            return self._token(T.BANG_EQ if self._match('=') else T.BANG)
        elif c == '=':
            return self._token(T.EQ_EQ if self._match('=') else T.EQ)
        elif c == '<':
            return self._token(T.LT_EQ if self._match('=') else T.LT)
        elif c == '>':
            return self._token(T.GT_EQ if self._match('=') else T.GT)
        elif c == '/':
            if self._match('/'):
                while self._peek() != '\n' and not self._at_end():
                    self._advance()
            else:
                return self._token(T.SLASH)
        elif c in ' \t\r\n':
            return None
        elif c == '"':
            return self._string()
        elif _isdigit(c):
            return self._number()
        elif _isalpha(c):
            return self._identifier()
        else:
            return self._error('Unexpected character')

    def _string(self) -> Token:
        # FIXME(klmr): Implement escape sequences.
        while self._peek() != '"' and not self._at_end():
            self._advance()
        if self._at_end():
            return self._error('Unterminated string')

        # Skip closing quote.
        self._advance()
        return self._token(T.STRING, self._source[self._start + 1 : self._pos - 1])

    def _number(self) -> Token:
        while _isdigit(self._peek()):
            self._advance()

        if self._peek() == '.' and _isdigit(self._peek_next()):
            self._advance()
            while _isdigit(self._peek()):
                self._advance()

        value = float(self._source[self._start : self._pos])
        return self._token(T.NUMBER, value)

    def _identifier(self) -> Token:
        while _isalnum(self._peek()):
            self._advance()

        ident = self._source[self._start : self._pos]
        return self._token(_KEYWORD_TOKENS.get(ident, T.IDENTIFIER))

    def _at_end(self) -> bool:
        return self._pos >= len(self._source)

    def _advance(self) -> str:
        pos = self._pos
        self._pos += 1
        return self._source[pos]

    def _match(self, expected: str) -> bool:
        if self._at_end():
            return False
        if self._source[self._pos] != expected:
            return False
        self._pos += 1
        return True

    def _peek(self) -> str:
        return '\0' if self._at_end() else self._source[self._pos]

    def _peek_next(self) -> str:
        return '\0' if self._pos + 1 >= len(self._source) else self._source[self._pos + 1]

    def _token(self, type: T, literal: object = None) -> Token:
        lexeme = self._source[self._start : self._pos]
        return Token(type, lexeme, literal, self._pos, self._pos - self._start)

    def _error(self, message: str) -> None:
        self._logger.scan_error(self._position(), message)

    def _position(self) -> Tuple[int, int]:
        return position_from_offset(self._source, self._pos)


def _isdigit(c: str) -> bool:
    return c >= '0' and c <= '9'


def _isalpha(c: str) -> bool:
    return (c >= 'a' and c <= 'z') or (c >= 'A' and c <= 'Z') or c == '_'


def _isalnum(c: str) -> bool:
    return _isalpha(c) or _isdigit(c)
