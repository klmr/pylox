from .log import MockLogger

from klmr.pylox.interpreter import Interpreter
from klmr.pylox.parser import parse
from klmr.pylox.scanner import scan


def run_test(code: str) -> None:
    logger = MockLogger()
    logger.reset(code)
    tokens = scan(code, logger)
    stmts = parse(tokens, logger)
    if logger.had_error:
        return
    Interpreter(logger).interpret(stmts)


def run_script_test(script_path: str) -> None:
    with open(script_path, 'r') as script:
        run_test(script.read())
