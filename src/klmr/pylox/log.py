import abc
import sys
from typing import Tuple

from .token import Token, TokenType


class Logger(abc.ABC):
    @abc.abstractmethod
    def scan_error(self, position: Tuple[int, int], message: str) -> None:
        pass

    @abc.abstractmethod
    def parse_error(self, token: Token, message: str) -> None:
        pass


class LoxLogger(Logger):
    def __init__(self) -> None:
        self.reset('')

    def reset(self, source: str) -> None:
        self.had_error = False
        self.source = source

    def scan_error(self, position: Tuple[int, int], message: str) -> None:
        self.report(position, '', message)

    def parse_error(self, token: Token, message: str) -> None:
        position = position_from_offset(self.source, token.offset)
        if token.type == TokenType.EOF:
            self.report(position, ' at end', message)
        else:
            self.report(position, f' at {token.lexeme}', message)

    def report(self, position: Tuple[int, int], where: str, message: str) -> None:
        line, col = position
        sys.stderr.write(f'[ln {line}/col {col}] Error{where}: {message}\n')
        self.had_error = True


def position_from_offset(source: str, offset: int) -> Tuple[int, int]:
    line, col = 1, 0
    for i in range(offset):
        if source[i] == '\n':
            line += 1
            col = 0
        else:
            col += 1

    return line, col
