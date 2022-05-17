from __future__ import annotations
import abc
from dataclasses import dataclass

from .token import Token, TokenType


# A type for AST node classes that have reference semantics (despite being data classes) and thus
# can be hashed and compared efficiently.
class AstNodeType(abc.ABCMeta):
    def __new__(mcls, name, bases, ns, **kwargs):
        cls = super().__new__(mcls, name, bases, ns, **kwargs)
        cls.__eq__ = lambda self, o: id(self) == id(o)
        cls.__hash__ = lambda self: id(self)
        return dataclass(eq = False)(cls)


class Expr(metaclass = AstNodeType):
    # Needed to silence spurious mypy warning.
    __match_args__ = ()


class Assign(Expr):
    name: Token
    value: Expr


class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr


class Call(Expr):
    callee: Expr
    paren: Token
    args: list[Expr]


class Get(Expr):
    object: Expr
    name: Token


class Grouping(Expr):
    expr: Expr


class Literal(Expr):
    value: object


class Logical(Expr):
    left: Expr
    operator: Token
    right: Expr


class Set(Expr):
    object: Expr
    name: Token
    value: Expr


class This(Expr):
    keyword: Token


class Unary(Expr):
    operator: Token
    operand: Expr


class Variable(Expr):
    name: Token


class Stmt(metaclass = AstNodeType):
    # Needed to silence spurious mypy warning.
    __match_args__ = ()


class Block(Stmt):
    stmts: list[Stmt]


class Class(Stmt):
    name: Token
    methods: list[FunctionStmt]


class ExprStmt(Stmt):
    expr: Expr


class FunctionStmt(Stmt):
    name: Token
    params: list[Token]
    body: list[Stmt]


class IfStmt(Stmt):
    cond: Expr
    then_branch: Stmt
    else_branch: Stmt | None


class PrintStmt(Stmt):
    expr: Expr


class ReturnStmt(Stmt):
    keyword: Token
    value: Expr | None


class VarStmt(Stmt):
    name: Token
    init: Expr | None


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
        case Get(object, name):
            return f'(. {format_ast(object)} {name.lexeme})'
        case Grouping(e):
            return f'(group {format_ast(e)})'
        case Literal(x):
            return str(x)
        case Logical(x):
            return f'({op.lexeme} {format_ast(left)} {format_ast(right)})'
        case Set(object, name, value):
            return f'(= (. {format_ast(object)} {name.lexeme}) {format_ast(value)})'
        case This(_):
            return 'this'
        case Unary(op, x):
            return f'({op.lexeme} {format_ast(x)})'
        case Variable(name):
            return name.lexeme

        case Block(stmts):
            stmts_fmt = ' '.join(format_ast(stmt) for stmt in stmts)
            return f'({{ {stmts_fmt})'
        case Class(name, methods):
            methods_fmt = ' '.join(format_ast(method) for method in methods)
            return f'(class {name.lexeme} {methods_fmt})'
        case ExprStmt(e):
            return format_ast(e)
        case FunctionStmt(name, params, body):
            params_fmt = ' '.join(param.lexeme for param in params)
            body_fmt = ' '.join(format_ast(stmt) for stmt in body)
            return f'(def {name.lexeme} ({params_fmt}) {body_fmt})'
        case IfStmt(c, t, e):
            else_fmt = format_ast(e) if e else ''
            return f'(if {format_ast(c)} {format_ast(t)} {else_fmt})'
        case PrintStmt(e):
            return f'(print {format_ast(e)})'
        case ReturnStmt(_, v):
            return f'(return {format_ast(v) if v else ""})'
        case VarStmt(name, init):
            init_fmt = f' {format_ast(init)}' if init is not None else ''
            return f'(var {name.lexeme}{init_fmt})'
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
