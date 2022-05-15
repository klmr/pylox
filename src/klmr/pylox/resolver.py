from enum import Enum
from .ast import (
    Assign, Binary, Block, Call, Expr, ExprStmt, FunctionStmt, Grouping, IfStmt, Literal, Logical, PrintStmt,
    ReturnStmt, Stmt, Unary, VarStmt, Variable, WhileStmt
)
from .interpreter import Interpreter
from .log import Logger
from .token import Token


def resolve(logger: Logger, interpreter: Interpreter, stmts: list[Stmt]) -> None:
    return Resolver(logger, interpreter).resolve_stmts(stmts)


class FunctionType(Enum):
    NONE = 0
    FUNCTION = 1


class Resolver:
    def __init__(self, logger: Logger, interpreter: Interpreter) -> None:
        self._scopes: list[dict[str, bool]] = []
        self._current_fun = FunctionType.NONE
        self._logger = logger
        self._interpreter = interpreter

    def resolve_stmts(self, stmts: list[Stmt]) -> None:
        for stmt in stmts:
            self.resolve(stmt)

    def resolve(self, x: Expr | Stmt | None) -> None:
        match x:
            case None:
                pass
            case Block(stmts):
                self._begin_scope()
                self.resolve_stmts(stmts)
                self._end_scope()
            case VarStmt(name, init):
                self._declare(name)
                self.resolve(init)
                self._define(name)
            case Variable(name):
                if self._scopes and self._scopes[-1].get(name.lexeme) is False:
                    self._logger.parse_error(name, 'Can’t read local variable in its own initializer')
                self._resolve_local(x, name)
            case Assign(name, value):
                self.resolve(value)
                self._resolve_local(x, name)
            case FunctionStmt(name, params, body):
                self._declare(name)
                self._define(name)
                self._resolve_fun(params, body, FunctionType.FUNCTION)
            case ExprStmt(expr):
                self.resolve(expr)
            case IfStmt(cond, then_branch, else_branch):
                self.resolve(cond)
                self.resolve(then_branch)
                self.resolve(else_branch)
            case PrintStmt(expr):
                self.resolve(expr)
            case ReturnStmt(keyword, value):
                if self._current_fun == FunctionType.NONE:
                    self._logger.parse_error(keyword, 'Can’t return from top-level code')
                self.resolve(value)
            case WhileStmt(cond, body):
                self.resolve(cond)
                self.resolve(body)
            case Binary(left, _, right):
                self.resolve(left)
                self.resolve(right)
            case Call(callee, _, args):
                self.resolve(callee)
                for arg in args:
                    self.resolve(arg)
            case Grouping(expr):
                self.resolve(expr)
            case Literal():
                pass
            case Logical(left, _, right):
                self.resolve(left)
                self.resolve(right)
            case Unary(_, expr):
                self.resolve(expr)

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

    def _resolve_fun(self, params: list[Token], body: list[Stmt], type: FunctionType) -> None:
        enclosing_fun = self._current_fun
        self._current_fun = type
        self._begin_scope()

        for param in params:
            self._declare(param)
            self._define(param)

        self.resolve_stmts(body)
        self._end_scope()
        self._current_fun = enclosing_fun
