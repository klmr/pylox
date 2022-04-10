from typing import Tuple

import klmr.pylox.log
from klmr.pylox.token import Token


class MockLogger(klmr.pylox.log.Logger):
    def scan_error(self, position: Tuple[int, int], message: str) -> None:
        raise ValueError(message)

    def parse_error(self, position: Tuple[int, int], token: Token, message: str) -> None:
        raise ValueError(message)

    def runtime_error(self, error: klmr.pylox.log.LoxRuntimeError) -> None:
        raise error
