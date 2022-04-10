from collections.abc import Iterable
from typing import cast

from .ast import Assign, Binary, Block, Expr, ExprStmt, Grouping, Literal, PrintStmt, Stmt, Unary, VarStmt, Variable
from .log import Logger, LoxLogger
from .token import Token, TokenType as TT


def parse(tokens: Iterable[Token], logger: Logger) -> list[Stmt]:
    return Parser(tokens, logger).parse()


class ParseError(RuntimeError):
    pass


class Parser:
    def __init__(self, tokens: Iterable[Token], logger: Logger) -> None:
        self._tokens = iter(tokens)
        self._curr = next(self._tokens)
        self._logger = logger

    def parse(self) -> list[Stmt]:
        '''
        program -> statement* EOF ;
        '''
        statements: list[Stmt] = []
        while not self._at_end():
            decl = self._declaration()
            if decl is not None:
                statements.append(decl)

        return statements

    def _declaration(self) -> Stmt | None:
        '''
        declaration -> var_decl
                     | statement ;
        '''
        try:
            if self._match_one_of(TT.VAR):
                return self._var_decl()
            else:
                return self._statement()
        except ParseError:
            self._synchronize()
            return None

    def _var_decl(self) -> Stmt:
        '''
        var_decl -> "var" IDENTIFIER ( "=" expression )? ";" ;
        '''
        name = self._consume(TT.IDENTIFIER, 'Expected variable name')
        init = self._expression() if self._match_one_of(TT.EQ) else None

        self._consume(TT.SEMICOLON, 'Expected \';\' after variable declaration')
        return VarStmt(name, init)

    def _statement(self) -> Stmt:
        '''
        statement -> expr_stmt
                   | print_stmt
                   | block ;
        '''
        if self._match_one_of(TT.PRINT):
            return self._print_statement()
        elif self._match_one_of(TT.LEFT_BRACE):
            return Block(self._block())
        else:
            return self._expression_statement()

    def _expression_statement(self) -> Stmt:
        '''
        expr_stmt -> expression ";" ;
        '''
        expr = self._expression()
        self._consume(TT.SEMICOLON, 'Expected \';\' after value')
        return ExprStmt(expr)

    def _print_statement(self) -> Stmt:
        '''
        print_stmt -> "print" expression ";" ;
        '''
        value = self._expression()
        self._consume(TT.SEMICOLON, 'Expected \';\' after value')
        return PrintStmt(value)

    def _block(self) -> list[Stmt]:
        '''
        block -> "{" declaration* "}" ;
        '''
        stmts: list[Stmt] = []
        while not self._check(TT.RIGHT_BRACE) and not self._at_end():
            decl = self._declaration()
            if decl is not None:
                stmts.append(decl)

        self._consume(TT.RIGHT_BRACE, 'Expected \'}\' after block')
        return stmts

    def _expression(self) -> Expr:
        '''
        expression -> assignment ;
        '''
        return self._assignment()

    def _assignment(self) -> Expr:
        '''
        assignment -> IDENTIFIER "=" assignment
                    | equality ;
        '''
        expr = self._equality()
        if eq := self._match_one_of(TT.EQ):
            value = self._assignment()

            if isinstance(expr, Variable):
                name = cast(Variable, expr).name
                return Assign(name, value)

            self._error(eq, f'Invalid assignment target {expr}')

        return expr

    def _equality(self) -> Expr:
        '''
        equality -> comparison ( ( "!=" | "==" ) comparison )* ;
        '''
        expr = self._comparison()
        while op := self._match_one_of(TT.BANG_EQ, TT.EQ_EQ):
            right = self._comparison()
            expr = Binary(expr, op, right)

        return expr

    def _comparison(self) -> Expr:
        '''
        comparison -> term ( ( ">" | ">=" | "<" | "<=" ) term )* ;
        '''
        expr = self._term()
        while op := self._match_one_of(TT.GT, TT.GT_EQ, TT.LT, TT.LT_EQ):
            right = self._term()
            expr = Binary(expr, op, right)

        return expr

    def _term(self) -> Expr:
        '''
        term -> factor ( ( "-" | "+" ) factor )* ;
        '''
        expr = self._factor()
        while op := self._match_one_of(TT.MINUS, TT.PLUS):
            right = self._factor()
            expr = Binary(expr, op, right)

        return expr

    def _factor(self) -> Expr:
        '''
        factor -> unary ( ( "/" | "*" ) unary )* ;
        '''
        expr = self._unary()
        while op := self._match_one_of(TT.SLASH, TT.STAR):
            right = self._unary()
            expr = Binary(expr, op, right)

        return expr

    def _unary(self) -> Expr:
        '''
        unary -> ("!" | "-" ) unary
               | "+" unary { error }
               | primary
        '''
        if op := self._match_one_of(TT.BANG, TT.MINUS):
            right = self._unary()
            return Unary(op, right)
        elif op := self._match_one_of(TT.PLUS):
            self._unary()
            raise self._error(op, 'Prefix-plus is not supported')
        else:
            return self._primary()

    def _primary(self) -> Expr:
        '''
        primary -> "true" | "false" | "nil"
                 | NUMBER | STRING
                 | IDENTIFIER
                 | "(" expression ")" ;
        '''
        if self._match_one_of(TT.FALSE):
            return Literal(False)
        elif self._match_one_of(TT.TRUE):
            return Literal(True)
        elif self._match_one_of(TT.NIL):
            return Literal(None)
        elif lit := self._match_one_of(TT.NUMBER, TT.STRING):
            return Literal(lit.literal)
        elif var := self._match_one_of(TT.IDENTIFIER):
            return Variable(var)
        elif self._match_one_of(TT.LEFT_PAREN):
            expr = self._expression()
            self._consume(TT.RIGHT_PAREN, 'Expected \')\' after expression')
            return Grouping(expr)

        raise self._error(self._curr, 'Expected expression.')

    def _match_one_of(self, *types: TT) -> Token | None:
        for type in types:
            if self._check(type):
                return self._advance()
        return None

    def _check(self, type: TT) -> bool:
        return self._curr.type == type

    def _advance(self) -> Token:
        curr = self._curr
        if not self._at_end():
            self._curr = next(self._tokens)
        return curr

    def _at_end(self) -> bool:
        return self._check(TT.EOF)

    def _consume(self, type: TT, error_msg: str) -> Token:
        if self._check(type):
            return self._advance()
        raise self._error(self._curr, error_msg)

    def _error(self, token: Token, error_msg: str) -> ParseError:
        self._logger.parse_error(token, error_msg)
        return ParseError()

    def _synchronize(self) -> None:
        prev = self._advance()
        while not self._at_end():
            if prev.type == TT.SEMICOLON:
                return

            if self._curr.type in (TT.CLASS, TT.FUN, TT.VAR, TT.FOR, TT.IF, TT.WHILE, TT.PRINT, TT.RETURN):
                return

            prev = self._advance()


if __name__ == '__main__':
    from .scanner import scan
    from .ast import format_ast
    import sys

    source = sys.stdin.read()
    logger = LoxLogger()
    logger.reset(source)
    stmts = parse(scan(source, logger), logger)
    for stmt in stmts:
        print(format_ast(stmt))
