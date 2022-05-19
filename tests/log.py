from klmr.pylox.log import Logger, LoxRuntimeError
from klmr.pylox.token import Token


class LoxSyntaxError(RuntimeError):
    pass


class MockLogger(Logger):
    def reset(self, source: str) -> None:
        pass

    def scan_error(self, position: tuple[int, int], message: str) -> None:
        row, col = position
        raise LoxSyntaxError(f'at ({row}, {col}): {message}')

    def parse_error(self, token: Token, message: str) -> None:
        raise LoxSyntaxError(f'at {token.lexeme}: {message}')

    def runtime_error(self, error: LoxRuntimeError) -> None:
        raise error
