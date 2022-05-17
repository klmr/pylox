from enum import Enum
from .ast import (
    Assign, Binary, Block, Call, Class, Expr, ExprStmt, FunctionStmt, Get, Grouping, IfStmt, Literal, Logical,
    PrintStmt, ReturnStmt, Set, Stmt, This, Unary, VarStmt, Variable, WhileStmt
)
from .interpreter import Interpreter
from .log import Logger
from .token import Token


def resolve(logger: Logger, interpreter: Interpreter, stmts: list[Stmt]) -> None:
    return Resolver(logger, interpreter).resolve_stmts(stmts)


class _ClassType(Enum):
    NONE = 0,
    CLASS = 1


class _FunctionType(Enum):
    NONE = 0
    FUNCTION = 1
    INITIALIZER = 2
    METHOD = 3


class Resolver:
    def __init__(self, logger: Logger, interpreter: Interpreter) -> None:
        self._scopes: list[dict[str, bool]] = []
        self._current_fun = _FunctionType.NONE
        self._current_class = _ClassType.NONE
        self._logger = logger
        self._interpreter = interpreter

    def resolve_stmts(self, stmts: list[Stmt]) -> None:
        for stmt in stmts:
            self.resolve(stmt)

    def resolve(self, x: Expr | Stmt | None) -> None:
        match x:
            case None | Literal():
                pass
            case Assign(name, value):
                self.resolve(value)
                self._resolve_local(x, name)
            case Binary(left, _, right):
                self.resolve(left)
                self.resolve(right)
            case Block(stmts):
                self._begin_scope()
                self.resolve_stmts(stmts)
                self._end_scope()
            case Call(callee, _, args):
                self.resolve(callee)
                for arg in args:
                    self.resolve(arg)
            case Class(name, methods):
                enclosing_class = self._current_class
                self._current_class = _ClassType.CLASS

                self._declare(name)
                self._define(name)

                self._begin_scope()
                self._scopes[-1]['this'] = True

                for method in methods:
                    decl = _FunctionType.INITIALIZER if method.name.lexeme == 'init' else _FunctionType.METHOD
                    self._resolve_fun(method.params, method.body, decl)

                self._end_scope()
                self._current_class = enclosing_class
            case ExprStmt(expr):
                self.resolve(expr)
            case FunctionStmt(name, params, body):
                self._declare(name)
                self._define(name)
                self._resolve_fun(params, body, _FunctionType.FUNCTION)
            case Get(object, _):
                self.resolve(object)
            case Grouping(expr):
                self.resolve(expr)
            case IfStmt(cond, then_branch, else_branch):
                self.resolve(cond)
                self.resolve(then_branch)
                self.resolve(else_branch)
            case Logical(left, _, right):
                self.resolve(left)
                self.resolve(right)
            case PrintStmt(expr):
                self.resolve(expr)
            case ReturnStmt(keyword, value):
                if self._current_fun == _FunctionType.NONE:
                    self._logger.parse_error(keyword, 'Can’t return from top-level code')
                if value and self._current_fun == _FunctionType.INITIALIZER:
                    self._logger.parse_error(keyword, 'Can’t return a value from an initializer')
                self.resolve(value)
            case Set(object, _, value):
                self.resolve(value)
                self.resolve(object)
            case This(keyword):
                if self._current_class == _ClassType.NONE:
                    self._logger.parse_error(keyword, 'Can’t use \'this\' outside of a class')
                self._resolve_local(x, keyword)
            case Unary(_, expr):
                self.resolve(expr)
            case Variable(name):
                if self._scopes and self._scopes[-1].get(name.lexeme) is False:
                    self._logger.parse_error(name, 'Can’t read local variable in its own initializer')
                self._resolve_local(x, name)
            case VarStmt(name, init):
                self._declare(name)
                self.resolve(init)
                self._define(name)
            case WhileStmt(cond, body):
                self.resolve(cond)
                self.resolve(body)

    def _begin_scope(self) -> None:
        self._scopes.append({})

    def _end_scope(self) -> None:
        self._scopes.pop()

    def _declare(self, name: Token) -> None:
        if not self._scopes:
            return

        scope = self._scopes[-1]
        if name.lexeme in scope:
            self._logger.parse_error(name, 'Already a variable with this name in scope')
        scope[name.lexeme] = False

    def _define(self, name: Token) -> None:
        if not self._scopes:
            return

        self._scopes[-1][name.lexeme] = True

    def _resolve_local(self, expr: Expr, name: Token) -> None:
        depth = len(self._scopes) - 1
        for i in range(depth, -1, -1):
            if name.lexeme in self._scopes[i]:
                self._interpreter.resolve(expr, depth - i)
                return

    def _resolve_fun(self, params: list[Token], body: list[Stmt], type: _FunctionType) -> None:
        enclosing_fun = self._current_fun
        self._current_fun = type
        self._begin_scope()

        for param in params:
            self._declare(param)
            self._define(param)

        self.resolve_stmts(body)
        self._end_scope()
        self._current_fun = enclosing_fun
