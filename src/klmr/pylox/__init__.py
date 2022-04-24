import sys

from .interpreter import Interpreter
from .log import LoxLogger
from .parser import parse
from .scanner import scan


PROMPT = '[REPL⟩ '

logger = LoxLogger()
interpreter = Interpreter(logger)


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
        run(script.read())
        if logger.had_error or logger.had_runtime_error:
            sys.exit(1)


def run_prompt() -> None:
    while True:
        try:
            run(input(PROMPT))
        except EOFError:
            break


def run(code: str) -> None:
    logger.reset(code)
    tokens = scan(code, logger)
    stmts = parse(tokens, logger)
    if logger.had_error:
        return
    interpreter.interpret(stmts)


if __name__ == '__main__':
    main()
