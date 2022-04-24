from klmr.pylox.log import Logger, LoxRuntimeError
from klmr.pylox.token import Token


class MockLogger(Logger):
    had_error = False

    def reset(self, source: str) -> None:
        pass

    def scan_error(self, position: tuple[int, int], message: str) -> None:
        raise ValueError(message)

    def parse_error(self, position: tuple[int, int], token: Token, message: str) -> None:
        raise ValueError(message)

    def runtime_error(self, error: LoxRuntimeError) -> None:
        raise error
