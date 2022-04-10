from typing import Dict, Final, Optional

from .log import LoxRuntimeError
from .token import Token


class Environment:
    def __init__(self, enclosing: Optional['Environment'] = None) -> None:
        self._enclosing: Final = enclosing
        self._bindings: Final[Dict[str, object]] = {}

    def define(self, name: str, value: object) -> None:
        self._bindings[name] = value

    def get(self, name: Token) -> object:
        try:
            return self._bindings[name.lexeme]
        except KeyError:
            if self._enclosing is not None:
                return self._enclosing.get(name)
            else:
                raise LoxRuntimeError(name, f'Undefined variable \'{name.lexeme}\'')

    def assign(self, name: Token, value: object) -> None:
        if name.lexeme in self._bindings:
            self._bindings[name.lexeme] = value
        elif self._enclosing is not None:
            self._enclosing.assign(name, value)
        else:
            raise RuntimeError(name, f'Undefined variable \'{name.lexeme}\'')
