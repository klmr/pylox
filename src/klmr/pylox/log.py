import sys


class Logger:
    def error(self, line: int, col: int, message: str) -> None:
        pass


class LoxLogger(Logger):
    def __init__(self) -> None:
        self.had_error = False

    def error(self, line: int, col: int, message: str) -> None:
        self.report(line, col, '', message)

    def report(self, line: int, col: int, where: str, message: str) -> None:
        sys.stderr.write(f'[ln {line}/col {col}] Error{where}: {message}\n')
        self.had_error = True
