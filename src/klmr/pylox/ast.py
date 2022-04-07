import abc
from dataclasses import dataclass

from .token import Token, TokenType


class Expr(abc.ABC):
    pass


@dataclass
class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr


@dataclass
class Unary(Expr):
    operator: Token
    operand: Expr


@dataclass
class Grouping(Expr):
    expr: Expr


@dataclass
class Literal(Expr):
    value: object


def format_ast(expr: Expr) -> str:
    match expr:
        case Binary(left, op, right):
            return f'({op.lexeme} {format_ast(left)} {format_ast(right)})'
        case Unary(op, x):
            return f'({op.lexeme} {format_ast(x)})'
        case Grouping(e):
            return f'(group {format_ast(e)})'
        case Literal(x):
            return f'{x}'
    assert False, 'Unhandled expr'


if __name__ == '__main__':
    def tok(type, lex, obj = None):
        return Token(type, lex, obj, 1, 1)

    # (-42) * (2 + 5)
    expr = Binary(
        Unary(tok(TokenType.MINUS, '-'), Literal(42)),
        tok(TokenType.STAR, '*'),
        Grouping(Binary(Literal(2), tok(TokenType.PLUS, '+'), Literal(5))),
    )

    print(format_ast(expr))
