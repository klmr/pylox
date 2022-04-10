import abc
from dataclasses import dataclass

from .token import Token, TokenType


class Expr(abc.ABC):
    pass


@dataclass
class Assign(Expr):
    name: Token
    value: Expr


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


@dataclass
class Variable(Expr):
    name: Token


class Stmt(abc.ABC):
    pass


@dataclass
class PrintStmt(Stmt):
    expr: Expr


@dataclass
class ExprStmt(Stmt):
    expr: Expr


@dataclass
class VarStmt(Stmt):
    name: Token
    init: Expr | None


@dataclass
class Block(Stmt):
    stmts: list[Stmt]


def format_ast(expr: Expr | Stmt) -> str:
    match expr:
        case Assign(name, value):
            return f'(= {name.lexeme} {format_ast(value)})'
        case Binary(left, op, right):
            return f'({op.lexeme} {format_ast(left)} {format_ast(right)})'
        case Unary(op, x):
            return f'({op.lexeme} {format_ast(x)})'
        case Grouping(e):
            return f'(group {format_ast(e)})'
        case Literal(x):
            return f'{x}'
        case Variable(name):
            return f'{name.length}'

        case PrintStmt(e):
            return f'(print {format_ast(e)})'
        case ExprStmt(e):
            return format_ast(e)
        case VarStmt(name, init):
            init_fmt = f' {format_ast(init)}' if init is not None else ''
            return f'(var {name.lexeme}{init_fmt})'
        case Block(stmts):
            stmts_fmt = ' '.join(format_ast(stmt) for stmt in stmts)
            return f'({{ {stmts_fmt})'

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
