from collections.abc import Iterable
from typing import cast

from .ast import (
    Assign, Binary, Block, Call, Expr, ExprStmt, FunctionStmt, Grouping, IfStmt, Literal, Logical, PrintStmt,
    ReturnStmt, Stmt, Unary, VarStmt, Variable, WhileStmt
)
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

    def parse_expression(self) -> Expr:
        return self._expression()

    def _declaration(self) -> Stmt | None:
        '''
        declaration -> var_decl
                     | fun_decl
                     | statement ;
        '''
        try:
            if self._match_one_of(TT.VAR):
                return self._var_decl()
            elif self._match_one_of(TT.FUN):
                return self._fun_decl("function")
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

    def _fun_decl(self, kind: str) -> Stmt:
        '''
        fun_decl -> "fun" function ;
        function -> IDENTIFIER "(" parameters? ")" block ;
        parameters -> IDENTIFIER ( "," IDENTIFIERS )* ;
        '''
        name = self._consume(TT.IDENTIFIER, f'Expected {kind} name')
        self._consume(TT.LEFT_PAREN, f'Expected \'(\' after {kind} name')
        params: list[Token] = []

        if not self._check(TT.RIGHT_PAREN):
            while True:
                if len(params) > 254:
                    self._error(self._curr, 'Can’t have more than 255 parameters')
                params.append(self._consume(TT.IDENTIFIER, 'Expected parameter name'))
                if not self._match_one_of(TT.COMMA):
                    break

        self._consume(TT.RIGHT_PAREN, 'Expected \')\' after parameters')
        self._consume(TT.LEFT_BRACE, f'Expected \'{{\' before {kind} body')
        body = self._block()
        return FunctionStmt(name, params, body)

    def _statement(self) -> Stmt:
        '''
        statement -> expr_stmt
                   | for_stmt
                   | if_stmt
                   | print_stmt
                   | return_stmt
                   | while_stmt
                   | block ;
        '''
        if self._match_one_of(TT.FOR):
            return self._for_statement()
        elif self._match_one_of(TT.IF):
            return self._if_statement()
        elif self._match_one_of(TT.PRINT):
            return self._print_statement()
        elif keyword := self._match_one_of(TT.RETURN):
            return self._return_statement(keyword)
        elif self._match_one_of(TT.WHILE):
            return self._while_statement()
        elif self._match_one_of(TT.LEFT_BRACE):
            return Block(self._block())
        else:
            return self._expression_statement()

    def _for_statement(self) -> Stmt:
        '''
        for_stmt -> "for" "("
                    ( var_decl | expr_stmt | ";" )
                    expression? ";"
                    expression? ")"
                    statement ;
        '''
        self._consume(TT.LEFT_PAREN, 'Expected \'(\' after \'for\'')

        if self._match_one_of(TT.SEMICOLON):
            init = None
        elif self._match_one_of(TT.VAR):
            init = self._var_decl()
        else:
            init = self._expression_statement()

        cond = self._expression() if not self._check(TT.SEMICOLON) else Literal(True)
        self._consume(TT.SEMICOLON, 'Expected \';\' after loop condition')

        incr = self._expression() if not self._check(TT.RIGHT_PAREN) else None
        self._consume(TT.RIGHT_PAREN, 'Expected \')\' after \'for\' clause')

        body = self._statement()

        if incr:
            body = Block([body, ExprStmt(incr)])

        body = WhileStmt(cond, body)

        if init:
            body = Block([init, body])

        return body

    def _if_statement(self) -> Stmt:
        '''
        if_stmt -> "if" "(" expression ")" statement ( "else" statement )? ;
        '''
        self._consume(TT.LEFT_PAREN, 'Expected \'(\' after \'if\'')
        cond = self._expression()
        self._consume(TT.RIGHT_PAREN, 'Expected \')\' after if condition')

        then_branch = self._statement()
        else_branch = self._statement() if self._match_one_of(TT.ELSE) else None

        return IfStmt(cond, then_branch, else_branch)

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

    def _return_statement(self, keyword: Token) -> Stmt:
        '''
        return_stmt -> "return" expression? ";" ;
        '''
        value = None if self._check(TT.SEMICOLON) else self._expression()
        self._consume(TT.SEMICOLON, 'Expected \';\' after return value')
        return ReturnStmt(keyword, value)

    def _while_statement(self) -> Stmt:
        '''
        while_stmt -> "while" "(" expression ")" statement ;
        '''
        self._consume(TT.LEFT_PAREN, 'Expected \'(\' after \'while\'')
        cond = self._expression()
        self._consume(TT.RIGHT_PAREN, 'Expected \')\' after loop condition')
        body = self._statement()

        return WhileStmt(cond, body)

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
                    | logical_or ;
        '''
        expr = self._or()
        if eq := self._match_one_of(TT.EQ):
            value = self._assignment()

            if isinstance(expr, Variable):
                name = cast(Variable, expr).name
                return Assign(name, value)

            self._error(eq, f'Invalid assignment target {expr}')

        return expr

    def _or(self) -> Expr:
        '''
        logical_or -> logical_and ( "or" logical_and )* ;
        '''
        expr = self._and()

        while op := self._match_one_of(TT.OR):
            right = self._and()
            expr = Logical(expr, op, right)

        return expr

    def _and(self) -> Expr:
        '''
        logical_and -> equality ( "and" equality )* ;
        '''
        expr = self._equality()

        while op := self._match_one_of(TT.AND):
            right = self._equality()
            expr = Logical(expr, op, right)

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
               | call
        '''
        if op := self._match_one_of(TT.BANG, TT.MINUS):
            right = self._unary()
            return Unary(op, right)
        elif op := self._match_one_of(TT.PLUS):
            self._unary()
            raise self._error(op, 'Prefix-plus is not supported')
        else:
            return self._call()

    def _call(self) -> Expr:
        '''
        call -> primary ( "(" arguments? ")" )* ;
        arguments -> expression ( "," expression )* ;
        '''
        expr = self._primary()

        while True:
            if self._match_one_of(TT.LEFT_PAREN):
                expr = self._finish_call(expr)
            else:
                break

        return expr

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

    def _finish_call(self, callee: Expr) -> Expr:
        args: list[Expr] = []

        if not self._check(TT.RIGHT_PAREN):
            while True:
                if len(args) > 254:
                    self._error(self._curr, 'Can’t have more than 255 arguments')
                args.append(self._expression())
                if not self._match_one_of(TT.COMMA):
                    break

        paren = self._consume(TT.RIGHT_PAREN, 'Expected \')\' after arguments')
        return Call(callee, paren, args)

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
