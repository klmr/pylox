from typing import cast

from .ast import Binary, Expr, Grouping, Literal, Unary
from .log import Logger, LoxRuntimeError
from .token import Token, TokenType


class Interpreter:
    def interpret(self, expr: Expr, logger: Logger) -> None:
        try:
            value = self._evaluate(expr)
            print(_stringify(value))
        except LoxRuntimeError as e:
            logger.runtime_error(e)

    def _evaluate(self, expr: Expr) -> object:
        match expr:
            case Literal(x):
                return x
            case Grouping(x):
                return self._evaluate(x)
            case Unary():
                return self._visit_unary(expr)
            case Binary():
                return self._visit_binary(expr)

        assert False, 'Unhandled expr'

    def _visit_unary(self, expr: Unary) -> object:
        operand = self._evaluate(expr.operand)

        match expr.operator.type:
            case TokenType.MINUS:
                _check_num_op(expr.operator, operand)
                return - _as_number(operand)
            case TokenType.BANG:
                return not _is_truthy(operand)
            case _:
                return None

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
            case _:
                return None


def _is_truthy(x: object) -> bool:
    match x:
        case None:
            return False
        case bool(x):
            return bool(x)
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
        case float(x):
            text = str(x)
            if text.endswith('.0'):
                text = text[: -2]
            return text
        case _:
            return str(x)
