from typing import Iterable, Optional, Tuple

from .log import Logger
from .token import Token, TokenType as T


def scan(source: str, logger: Logger) -> Iterable[Token]:
    return _Scanner(source, logger).tokens()


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


class _Scanner:
    def __init__(self, source: str, logger: Logger) -> None:
        self.source = source
        self.logger = logger
        self.start = 0
        self.pos = 0

    def tokens(self) -> Iterable[Token]:
        while not self.at_end():
            self.start = self.pos
            token = self.scan_token()
            if token:
                yield token
        yield Token(T.EOF, '', None, self.pos, 0)

    def scan_token(self) -> Optional[Token]:
        c = self.advance()
        if c == '(':
            return self.token(T.LEFT_PAREN)
        elif c == ')':
            return self.token(T.RIGHT_PAREN)
        elif c == '{':
            return self.token(T.LEFT_BRACE)
        elif c == '}':
            return self.token(T.RIGHT_BRACE)
        elif c == ',':
            return self.token(T.COMMA)
        elif c == '.':
            return self.token(T.DOT)
        elif c == '-':
            return self.token(T.MINUS)
        elif c == '+':
            return self.token(T.PLUS)
        elif c == ';':
            return self.token(T.SEMICOLON)
        elif c == '*':
            return self.token(T.STAR)
        elif c == '!':
            return self.token(T.BANG_EQ if self.match('=') else T.BANG)
        elif c == '=':
            return self.token(T.EQ_EQ if self.match('=') else T.EQ)
        elif c == '<':
            return self.token(T.LT_EQ if self.match('=') else T.LT)
        elif c == '>':
            return self.token(T.GT_EQ if self.match('=') else T.GT)
        elif c == '/':
            if self.match('/'):
                while self.peek() != '\n' and not self.at_end():
                    self.advance()
            else:
                return self.token(T.SLASH)
        elif c in ' \t\r\n':
            return None
        elif c == '"':
            return self.string()
        elif isdigit(c):
            return self.number()
        elif isalpha(c):
            return self.identifier()
        else:
            return self.error('Unexpected character')

    def string(self) -> Token:
        # FIXME(klmr): Implement escape sequences.
        while self.peek() != '"' and not self.at_end():
            self.advance()
        if self.at_end():
            return self.error('Unterminated string')

        # Skip closing quote.
        self.advance()
        return self.token(T.STRING, self.source[self.start + 1 : self.pos - 1])

    def number(self) -> Token:
        while isdigit(self.peek()):
            self.advance()

        if self.peek() == '.' and isdigit(self.peek_next()):
            self.advance()
            while isdigit(self.peek()):
                self.advance()

        value = float(self.source[self.start : self.pos])
        return self.token(T.NUMBER, value)

    def identifier(self) -> Token:
        while isalnum(self.peek()):
            self.advance()

        ident = self.source[self.start : self.pos]
        return self.token(_KEYWORD_TOKENS.get(ident, T.IDENTIFIER))

    def at_end(self) -> bool:
        return self.pos >= len(self.source)

    def advance(self) -> str:
        pos = self.pos
        self.pos += 1
        return self.source[pos]

    def match(self, expected: str) -> bool:
        if self.at_end():
            return False
        if self.source[self.pos] != expected:
            return False
        self.pos += 1
        return True

    def peek(self) -> str:
        return '\0' if self.at_end() else self.source[self.pos]

    def peek_next(self) -> str:
        return '\0' if self.pos + 1 >= len(self.source) else self.source[self.pos + 1]

    def token(self, type: T, literal: object = None) -> Token:
        lexeme = self.source[self.start : self.pos]
        return Token(type, lexeme, literal, self.pos, self.pos - self.start)

    def error(self, message: str) -> None:
        line, col = self.position()
        self.logger.error(line, col, message)

    def position(self) -> Tuple[int, int]:
        line, col = 1, 0
        for i in range(self.pos):
            if self.source[i] == '\n':
                line += 1
                col = 0
            else:
                col += 1

        return line, col


def isdigit(c: str) -> bool:
    return c >= '0' and c <= '9'


def isalpha(c: str) -> bool:
    return (c >= 'a' and c <= 'z') or (c >= 'A' and c <= 'Z') or c == '_'


def isalnum(c: str) -> bool:
    return isalpha(c) or isdigit(c)
