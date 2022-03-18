import abc
from typing import Generic, TypeVar

from .token import Token, TokenType


R = TypeVar('R')


class Expr(abc.ABC):
    def accept(self, visitor: 'Visitor[R]') -> R:
        myclass = type(self).__name__.lower()
        return getattr(visitor, f'visit_{myclass}')(self)


class Binary(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr) -> None:
        super().__init__()
        self.left = left
        self.operator = operator
        self.right = right

    def __repr__(self) -> str:
        return f'Binary({self.left!r}, {self.operator!r}, {self.right!r})'


class Unary(Expr):
    def __init__(self, operator: Token, operand: Expr) -> None:
        super().__init__()
        self.operator = operator
        self.operand = operand

    def __repr__(self) -> str:
        return f'Unary({self.operator!r}, {self.operand!r})'


class Grouping(Expr):
    def __init__(self, expr: Expr) -> None:
        super().__init__()
        self.expr = expr

    def __repr__(self) -> str:
        return f'Grouping({self.expr!r})'


class Literal(Expr):
    def __init__(self, value: object) -> None:
        super().__init__()
        self.value = value

    def __repr__(self) -> str:
        return f'Literal({self.value!r})'


class Visitor(abc.ABC, Generic[R]):
    @abc.abstractmethod
    def visit_binary(self, expr: Binary) -> R:
        pass

    @abc.abstractmethod
    def visit_unary(self, expr: Unary) -> R:
        pass

    @abc.abstractmethod
    def visit_grouping(self, expr: Grouping) -> R:
        pass

    @abc.abstractmethod
    def visit_literal(self, expr: Literal) -> R:
        pass


class AstPrinter(Visitor[str]):
    def print(self, expr: Expr) -> str:
        return expr.accept(self)

    def visit_binary(self, expr: Binary) -> str:
        return f'({expr.operator.lexeme} {expr.left.accept(self)} {expr.right.accept(self)})'

    def visit_unary(self, expr: Unary) -> str:
        return f'({expr.operator.lexeme} {expr.operand.accept(self)})'

    def visit_grouping(self, expr: Grouping) -> str:
        return f'(group {expr.expr.accept(self)})'

    def visit_literal(self, expr: Literal) -> str:
        return f'{expr.value}'


def print_ast(expr: Expr) -> str:
    return AstPrinter().print(expr)


if __name__ == '__main__':
    def tok(type, lex, obj = None):
        return Token(type, lex, obj, 1, 1)

    # (-42) * (2 + 5)
    expr = Binary(
        Unary(tok(TokenType.MINUS, '-'), Literal(42)),
        tok(TokenType.STAR, '*'),
        Grouping(Binary(Literal(2), tok(TokenType.PLUS, '+'), Literal(5))),
    )

    print(print_ast(expr))
