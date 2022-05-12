from klmr.pylox.log import Logger, LoxRuntimeError
from klmr.pylox.token import Token


class MockLogger(Logger):
    def reset(self, source: str) -> None:
        pass

    def scan_error(self, position: tuple[int, int], message: str) -> None:
        row, col = position
        raise ValueError(f'at ({row}, {col}): {message}')

    def parse_error(self, token: Token, message: str) -> None:
        raise ValueError(f'at {token.lexeme}: {message}')

    def runtime_error(self, error: LoxRuntimeError) -> None:
        raise error
