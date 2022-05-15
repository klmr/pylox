from __future__ import annotations
import abc
from collections.abc import Callable
from inspect import signature
import time
from typing import Concatenate, ParamSpec, cast

from .ast import (
    Assign, Binary, Block, Call, Expr, ExprStmt, FunctionStmt, Grouping, IfStmt, Literal, Logical, PrintStmt,
    ReturnStmt, Stmt, Unary, VarStmt, Variable, WhileStmt
)
from .environment import Environment
from .log import Logger, LoxRuntimeError
from .parser import Parser
from .scanner import scan
from .token import Token, TokenType


class Return(BaseException):
    def __init__(self, value: object) -> None:
        self.value = value


class LoxCallable(abc.ABC):
    @property
    @abc.abstractmethod
    def arity(self) -> int:
        pass

    @abc.abstractmethod
    def __call__(self, interpreter: Interpreter, args: list[object]) -> object:
        pass


class LoxFunction(LoxCallable):
    def __init__(self, decl: FunctionStmt, enclosing: Environment) -> None:
        self._decl = decl
        self._enclosing = enclosing

    @property
    def arity(self) -> int:
        return len(self._decl.params)

    def __call__(self, interpreter: Interpreter, args: list[object]) -> object:
        env = Environment(self._enclosing)
        for param, arg in zip(self._decl.params, args):
            env.define(param.lexeme, arg)

        try:
            interpreter._execute_block(self._decl.body, env)
        except Return as ret:
            return ret.value
        return None

    def __str__(self) -> str:
        return f'‹fun {self._decl.name.lexeme}›'


class Interpreter:
    def __init__(self, logger: Logger) -> None:
        self._globals = Environment()
        self._env = self._globals
        self._locals: dict[Expr, int] = {}
        self._logger = logger

        for name, fun in _native_funs.items():
            self._globals.define(name, fun)

    def interpret(self, stmts: list[Stmt]) -> None:
        try:
            for stmt in stmts:
                self._execute(stmt)
        except LoxRuntimeError as e:
            self._logger.runtime_error(e)

    def eval(self, code: str) -> object:
        try:
            expr = Parser(scan(code, self._logger), self._logger).parse_expression()
            return self._evaluate(expr)
        except LoxRuntimeError as e:
            self._logger.runtime_error(e)
            return None

    def resolve(self, expr: Expr, depth: int) -> None:
        self._locals[expr] = depth

    def _execute(self, stmt: Stmt) -> None:
        match stmt:
            case Block(stmts):
                self._execute_block(stmts, Environment(self._env))
            case ExprStmt(expr):
                self._evaluate(expr)
            case FunctionStmt(name, _, _) as fdef:
                function = LoxFunction(fdef, self._env)
                self._env.define(name.lexeme, function)
            case IfStmt(cond, then_branch, else_branch):
                if _is_truthy(self._evaluate(cond)):
                    self._execute(then_branch)
                elif else_branch:
                    self._execute(else_branch)
            case PrintStmt(expr):
                value = self._evaluate(expr)
                print(_stringify(value))
            case ReturnStmt(_, expr):
                value = None if expr is None else self._evaluate(expr)
                raise Return(value)
            case VarStmt(name, init):
                value = self._evaluate(init) if init is not None else None
                self._env.define(name.lexeme, value)
            case WhileStmt(cond, body):
                while _is_truthy(self._evaluate(cond)):
                    self._execute(body)

    def _execute_block(self, stmts: list[Stmt], env: Environment) -> None:
        prev = self._env
        try:
            self._env = env
            for stmt in stmts:
                self._execute(stmt)
        finally:
            self._env = prev

    def _evaluate(self, expr: Expr) -> object:
        match expr:
            case Assign(name, e):
                value = self._evaluate(e)
                self._assign_variable(name, expr, value)
                return value
            case Binary():
                return self._visit_binary(expr)
            case Call():
                return self._visit_call(expr)
            case Literal(x):
                return x
            case Logical():
                return self._visit_logical(expr)
            case Grouping(x):
                return self._evaluate(x)
            case Unary():
                return self._visit_unary(expr)
            case Variable(name):
                return self._lookup_variable(name, expr)

        assert False, 'Unhandled expr'

    def _visit_unary(self, expr: Unary) -> object:
        operand = self._evaluate(expr.operand)

        match expr.operator.type:
            case TokenType.MINUS:
                _check_num_op(expr.operator, operand)
                return - _as_number(operand)
            case TokenType.BANG:
                return not _is_truthy(operand)

        assert False, 'Unhandled unary operator'

    def _visit_binary(self, expr: Binary) -> object:
        left = self._evaluate(expr.left)
        right = self._evaluate(expr.right)
        op = expr.operator

        match op.type:
            case TokenType.LT:
                _check_num_ops(op, left, right)
                return _as_number(left) < _as_number(right)
            case TokenType.LT_EQ:
                _check_num_ops(op, left, right)
                return _as_number(left) <= _as_number(right)
            case TokenType.GT:
                _check_num_ops(op, left, right)
                return _as_number(left) > _as_number(right)
            case TokenType.GT_EQ:
                _check_num_ops(op, left, right)
                return _as_number(left) >= _as_number(right)
            case TokenType.EQ_EQ:
                return _is_equal(left, right)
            case TokenType.BANG_EQ:
                return not _is_equal(left, right)
            case TokenType.MINUS:
                _check_num_ops(op, left, right)
                return _as_number(left) - _as_number(right)
            case TokenType.SLASH:
                _check_num_ops(op, left, right)
                if _as_number(right) == 0:
                    raise LoxRuntimeError(op, 'Cannot divide by zero')
                return _as_number(left) / _as_number(right)
            case TokenType.STAR:
                _check_num_ops(op, left, right)
                return _as_number(left) * _as_number(right)
            case TokenType.PLUS:
                if isinstance(left, float) and isinstance(right, float):
                    return _as_number(left) + _as_number(right)
                elif isinstance(left, str) and isinstance(right, str):
                    return f'{left}{right}'

                raise LoxRuntimeError(op, 'Operands must be two numbers or two strings')

        assert False, 'Unhandled binary operator'

    def _visit_logical(self, expr: Logical) -> object:
        left = self._evaluate(expr.left)
        op = expr.operator

        match op.type:
            case TokenType.OR:
                if _is_truthy(left):
                    return left
            case TokenType.AND:
                if not _is_truthy(left):
                    return left

        return self._evaluate(expr.right)

    def _visit_call(self, expr: Call) -> object:
        callee = self._evaluate(expr.callee)

        args = [self._evaluate(arg) for arg in expr.args]

        if not isinstance(callee, LoxCallable):
            raise LoxRuntimeError(expr.paren, 'Can only call functions and classes')

        if len(args) != callee.arity:
            raise LoxRuntimeError(expr.paren, f'Expected {callee.arity} arguments but got {len(args)}')
        return callee(self, args)

    def _lookup_variable(self, name: Token, expr: Expr) -> object:
        dist = self._locals.get(expr)
        if dist is not None:
            return self._env.get_at(dist, name.lexeme)
        else:
            return self._globals.get(name)

    def _assign_variable(self, name: Token, expr: Expr, value: object) -> None:
        dist = self._locals.get(expr)
        if dist is not None:
            self._env.assign_at(dist, name, value)
        else:
            self._globals.assign(name, value)


def _is_truthy(x: object) -> bool:
    match x:
        case None:
            return False
        case bool(b):
            return b
        case _:
            return True


def _is_equal(x: object, y: object) -> bool:
    match x, y:
        case None, None:
            return True
        case None, _:
            return False
        case _:
            return x == y


def _as_number(x: object) -> float:
    return float(cast(float, x))


def _check_num_op(op: Token, x: object) -> None:
    if not isinstance(x, float):
        raise LoxRuntimeError(op, 'Operand must be a number')


def _check_num_ops(op: Token, left: object, right: object) -> None:
    if not (isinstance(left, float) and isinstance(right, float)):
        raise LoxRuntimeError(op, 'Operands must be numbers')


def _stringify(x: object) -> str:
    match x:
        case None:
            return 'nil'
        case False:
            return 'false'
        case True:
            return 'true'
        case float():
            text = str(x)
            if text.endswith('.0'):
                text = text[: -2]
            return text
        case _:
            return str(x)


P = ParamSpec('P')


_native_funs: dict[str, LoxCallable] = {}


# FIXME: This currently doesn’t typecheck in mypy because support for `Concatenate` *just* got
# merged (https://github.com/python/mypy/pull/11847). However, I think it’s correct.
class native_fun_wrapper(LoxCallable):
    def __init__(self, fun: Callable[Concatenate[Interpreter, P], object]) -> None:  # type: ignore[misc]
        self._fun = fun
        self._arity = len(signature(fun).parameters) - 1

    @property
    def arity(self) -> int:
        return self._arity

    def __call__(self, interpreter: 'Interpreter', args: list[object]) -> object:
        return self._fun(interpreter, *args)

    def __str__(self) -> str:
        return '‹native fun›'


def native_fun(fun: Callable[Concatenate[Interpreter, P], object]) -> LoxCallable:  # type: ignore[misc]
    wrapped = native_fun_wrapper(fun)
    _native_funs[fun.__name__[5:]] = wrapped
    return fun


@native_fun
def _lox_clock(interpreter: Interpreter) -> object:
    return time.time()


@native_fun
def _lox_printf(interpreter: Interpreter, format: str) -> object:
    import re

    formatted = ''
    for i, split in enumerate(re.split(r'\{([^}]+)\}', format)):
        if i % 2 == 0:
            formatted += split
        else:
            formatted += _stringify(interpreter.eval(split))

    print(formatted)
    return None
