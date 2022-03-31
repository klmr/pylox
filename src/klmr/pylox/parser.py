from typing import Iterable, Optional

from .ast import Binary, Expr, Grouping, Literal, Unary
from .log import Logger, LoxLogger
from .token import Token, TokenType as TT


def parse(tokens: Iterable[Token], logger: Logger) -> Expr:
    return Parser(tokens, logger).parse()


class ParseError(RuntimeError):
    pass


class Parser:
    def __init__(self, tokens: Iterable[Token], logger: Logger) -> None:
        self._tokens = tokens
        # FIXME(klmr): Why can’t pyright infer the type of `self._curr` here?
        self._curr: Token = next(self._tokens)
        self._logger = logger

    def parse(self) -> Optional[Expr]:
        # FIXME(klmr): Ensure that the parser has consumed all tokens.
        try:
            return self._expression()
        except ParseError:
            return None

    def _expression(self) -> Expr:
        '''
        expression -> equality ;
        '''
        return self._equality()

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
        primary -> "true" | "false" | "nil" | NUMBER | STRING
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
        elif self._match_one_of(TT.LEFT_PAREN):
            expr = self._expression()
            self._consume(TT.RIGHT_PAREN, 'Expected \')\' after expression')
            return Grouping(expr)

        raise self._error(self._curr, 'Expected expression.')

    def _match_one_of(self, *types: TT) -> Optional[Token]:
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
    from .ast import print_ast
    import sys

    source = sys.stdin.read()
    logger = LoxLogger()
    logger.reset(source)
    expr = parse(scan(source, logger), logger)
    if not logger.had_error:
        print(print_ast(expr))
