from .ast import Binary, Expr, Grouping, Literal, Unary, Visitor
from .log import Logger, LoxRuntimeError
from .token import Token, TokenType


class Interpreter(Visitor[object]):
    def interpret(self, expr: Expr, logger: Logger) -> None:
        try:
            value = self._evaluate(expr)
            print(_stringify(value))
        except LoxRuntimeError as e:
            logger.runtime_error(e)

    def visit_literal(self, expr: Literal) -> object:
        return expr.value

    def visit_unary(self, expr: Unary) -> object:
        operand = self._evaluate(expr.operand)

        if expr.operator.type == TokenType.MINUS:
            _check_num_op(expr.operator, operand)
            return - float(operand)
        elif expr.operator.type == TokenType.BANG:
            return not _is_truthy(operand)

        return None

    def visit_binary(self, expr: Binary) -> object:
        left = self._evaluate(expr.left)
        right = self._evaluate(expr.right)
        op = expr.operator
        type = op.type

        if type == TokenType.LT:
            _check_num_ops(op, left, right)
            return float(left) < float(right)
        elif type == TokenType.LT_EQ:
            _check_num_ops(op, left, right)
            return float(left) <= float(right)
        elif type == TokenType.GT:
            _check_num_ops(op, left, right)
            return float(left) > float(right)
        elif type == TokenType.GT_EQ:
            _check_num_ops(op, left, right)
            return float(left) >= float(right)
        elif type == TokenType.EQ:
            return _is_equal(left, right)
        elif type == TokenType.BANG_EQ:
            return not _is_equal(left, right)
        elif type == TokenType.MINUS:
            _check_num_ops(op, left, right)
            return float(left) - float(right)
        elif type == TokenType.SLASH:
            _check_num_ops(op, left, right)
            if float(right) == 0:
                raise LoxRuntimeError(op, 'Cannot divide by zero')
            return float(left) / float(right)
        elif type == TokenType.STAR:
            _check_num_ops(op, left, right)
            return float(left) * float(right)
        elif type == TokenType.PLUS:
            if isinstance(left, float) and isinstance(right, float):
                return float(left) + float(right)
            elif isinstance(left, str) and isinstance(right, str):
                return f'{left}{right}'

            raise LoxRuntimeError(op, 'Operands must be two numbers or two strings')

        return None

    def visit_grouping(self, expr: Grouping) -> object:
        return self._evaluate(expr.expr)

    def _evaluate(self, expr: Expr) -> object:
        return expr.accept(self)


def _is_truthy(x: object) -> bool:
    if x is None:
        return False
    elif isinstance(x, bool):
        return bool(x)
    else:
        return True


def _is_equal(x: object, y: object) -> bool:
    if x is None and y is None:
        return True
    elif x is None:
        return False
    return x == y


def _check_num_op(op: Token, x: object) -> None:
    if not isinstance(x, float):
        raise LoxRuntimeError(op, 'Operand must be a number')


def _check_num_ops(op: Token, left: object, right: object) -> None:
    if not (isinstance(left, float) and isinstance(right, float)):
        raise LoxRuntimeError(op, 'Operands must be numbers')


def _stringify(x: object) -> None:
    if x is None:
        return 'nil'

    if isinstance(x, float):
        text = str(x)
        if text.endswith('.0'):
            text = text[: -2]
        return text

    return str(x)
