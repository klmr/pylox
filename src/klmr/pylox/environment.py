from __future__ import annotations
from typing import Final, cast

from .log import LoxRuntimeError
from .token import Token


class Environment:
    def __init__(self, enclosing: Environment | None = None) -> None:
        self.enclosing: Final = enclosing
        self._bindings: Final[dict[str, object]] = {}

    def define(self, name: str, value: object) -> None:
        self._bindings[name] = value

    def get(self, name: Token) -> object:
        try:
            return self._bindings[name.lexeme]
        except KeyError:
            if self.enclosing is not None:
                return self.enclosing.get(name)
            else:
                raise LoxRuntimeError(name, f'Undefined variable \'{name.lexeme}\'')

    def get_at(self, dist: int, name: str) -> object:
        return self._ancestor(dist)._bindings[name]

    def assign(self, name: Token, value: object) -> None:
        if name.lexeme in self._bindings:
            self._bindings[name.lexeme] = value
        elif self.enclosing is not None:
            self.enclosing.assign(name, value)
        else:
            raise LoxRuntimeError(name, f'Undefined variable \'{name.lexeme}\'')

    def assign_at(self, dist: int, name: Token, value: object) -> None:
        self._ancestor(dist)._bindings[name.lexeme] = value

    def _ancestor(self, dist: int) -> Environment:
        env = self
        for _ in range(dist):
            env = cast(Environment, env.enclosing)
        return env
