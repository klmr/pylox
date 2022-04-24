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
class Call(Expr):
    callee: Expr
    paren: Token
    args: list[Expr]


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
class Logical(Expr):
    left: Expr
    operator: Token
    right: Expr


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
class FunctionStmt(Stmt):
    name: Token
    params: list[Token]
    body: list[Stmt]


@dataclass
class IfStmt(Stmt):
    cond: Expr
    then_branch: Stmt
    else_branch: Stmt | None


@dataclass
class VarStmt(Stmt):
    name: Token
    init: Expr | None


@dataclass
class ReturnStmt(Stmt):
    keyword: Token
    value: Expr


@dataclass
class Block(Stmt):
    stmts: list[Stmt]


@dataclass
class WhileStmt(Stmt):
    cond: Expr
    body: Stmt


def format_ast(expr: Expr | Stmt) -> str:
    match expr:
        case Assign(name, value):
            return f'(= {name.lexeme} {format_ast(value)})'
        case Binary(left, op, right):
            return f'({op.lexeme} {format_ast(left)} {format_ast(right)})'
        case Call(callee, _, args):
            args_fmt = ' '.join(format_ast(arg) for arg in args)
            return f'({format_ast(callee)} {args_fmt})'
        case Unary(op, x):
            return f'({op.lexeme} {format_ast(x)})'
        case Grouping(e):
            return f'(group {format_ast(e)})'
        case Literal(x):
            return str(x)
        case Logical(x):
            return f'({op.lexeme} {format_ast(left)} {format_ast(right)})'
        case Variable(name):
            return name.lexeme

        case PrintStmt(e):
            return f'(print {format_ast(e)})'
        case ExprStmt(e):
            return format_ast(e)
        case FunctionStmt(name, params, body):
            params_fmt = ' '.join(param.lexeme for param in params)
            body_fmt = ' '.join(format_ast(stmt) for stmt in body)
            return f'(def {name.lexeme} ({params_fmt}) {body_fmt})'
        case IfStmt(c, t, e):
            else_fmt = format_ast(e) if e else ''
            return f'(if {format_ast(c)} {format_ast(t)} {else_fmt})'
        case ReturnStmt(_, v):
            return f'(return {format_ast(v)})'
        case VarStmt(name, init):
            init_fmt = f' {format_ast(init)}' if init is not None else ''
            return f'(var {name.lexeme}{init_fmt})'
        case Block(stmts):
            stmts_fmt = ' '.join(format_ast(stmt) for stmt in stmts)
            return f'({{ {stmts_fmt})'
        case WhileStmt(cond, stmt):
            return f'(while {format_ast(cond)} {format_ast(stmt)})'

    assert False, 'Unhandled expr'


if __name__ == '__main__':
    def tok(type, lex, obj = None):
        return Token(type, lex, obj, 1, 1)

    # {
    #   var answer = 42;
    #   print - answer * (2 + 5);
    # }
    expr = Block([
        VarStmt(
            tok(TokenType.IDENTIFIER, 'answer'),
            Literal(42)
        ),
        PrintStmt(Binary(
            Unary(
                tok(TokenType.MINUS, '-'),
                Variable(tok(TokenType.IDENTIFIER, 'answer'))
            ),
            tok(TokenType.STAR, '*'),
            Grouping(Binary(Literal(2), tok(TokenType.PLUS, '+'), Literal(5)))
        ))
    ])

    print(format_ast(expr))
