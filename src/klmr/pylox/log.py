import abc
import sys
from typing import Tuple

from .token import Token, TokenType


class LoxRuntimeError(RuntimeError):
    def __init__(self, op: Token, msg: str) -> None:
        super().__init__(msg)
        self.op = op


class Logger(abc.ABC):
    @abc.abstractmethod
    def scan_error(self, position: Tuple[int, int], message: str) -> None:
        pass

    @abc.abstractmethod
    def parse_error(self, token: Token, message: str) -> None:
        pass

    @abc.abstractmethod
    def runtime_error(self, error: LoxRuntimeError) -> None:
        pass


class LoxLogger(Logger):
    def __init__(self) -> None:
        self.reset('')

    def reset(self, source: str) -> None:
        self.had_error = False
        self.had_runtime_error = False
        self.source = source

    def scan_error(self, position: Tuple[int, int], message: str) -> None:
        self._report(position, '', message)

    def parse_error(self, token: Token, message: str) -> None:
        position = position_from_offset(self.source, token.offset)
        if token.type == TokenType.EOF:
            self._report(position, ' at end', message)
        else:
            self._report(position, f' at {token.lexeme}', message)

    def runtime_error(self, error: LoxRuntimeError) -> None:
        line, col = position_from_offset(self.source, error.op.offset)
        sys.stderr.write(f'[ln {line}/col {col}] Error: {error}\n')
        self.had_runtime_error = True

    def _report(self, position: Tuple[int, int], where: str, message: str) -> None:
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
