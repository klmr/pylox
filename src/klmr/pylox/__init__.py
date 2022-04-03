import sys

from .interpreter import Interpreter
from .parser import parse
from .log import LoxLogger
from .scanner import scan


PROMPT = '[REPL⟩ '

interpreter = Interpreter()
logger = LoxLogger()


def main() -> None:
    if len(sys.argv) > 2:
        sys.stderr.write(f'Usage: {sys.argv[0]} [script]\n')
        sys.exit(1)

    if len(sys.argv) == 2:
        run_script(sys.argv[1])
    else:
        run_prompt()


def run_script(script_path: str) -> None:
    with open(script_path, 'r') as script:
        run(script.read(), logger)
        if logger.had_error or logger.had_runtime_error:
            sys.exit(1)


def run_prompt() -> None:
    while True:
        try:
            run(input(PROMPT), logger)
        except EOFError:
            break


def run(expr: str, logger: LoxLogger) -> None:
    logger.reset(expr)
    tokens = scan(expr, logger)
    expr = parse(tokens, logger)
    if logger.had_error:
        return
    interpreter.interpret(expr, logger)


if __name__ == '__main__':
    main()
