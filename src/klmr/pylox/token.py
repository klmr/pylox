import enum


class AutoIncrement(enum.Enum):
    def __new__(cls, *args):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj


class TokenType(AutoIncrement):
    LEFT_PAREN = ()
    RIGHT_PAREN = ()
    LEFT_BRACE = ()
    RIGHT_BRACE = ()
    COMMA = ()
    DOT = ()
    MINUS = ()
    PLUS = ()
    SEMICOLON = ()
    SLASH = ()
    STAR = ()

    BANG = ()
    BANG_EQ = ()
    EQ = ()
    EQ_EQ = ()
    GT = ()
    GT_EQ = ()
    LT = ()
    LT_EQ = ()

    # Literals.
    IDENTIFIER = ()
    STRING = ()
    NUMBER = ()

    # Keywords.
    AND = ()
    CLASS = ()
    ELSE = ()
    FALSE = ()
    FUN = ()
    FOR = ()
    IF = ()
    NIL = ()
    OR = ()
    PRINT = ()
    RETURN = ()
    SUPER = ()
    THIS = ()
    TRUE = ()
    VAR = ()
    WHILE = ()

    EOF = ()

    def __repr__(self) -> str:
        return f'<{type(self).__name__}.{self.name}>'


class Token:
    def __init__(self, type: TokenType, lexeme: str, literal: object, offset: int, length: int) -> None:
        self.type = type
        self.lexeme = lexeme
        self.literal = literal
        self.offset = offset
        self.length = length

    def __str__(self) -> str:
        return f'{self.type.name} {self.lexeme!r} {self.literal!r}'

    def __repr__(self) -> str:
        return f'Token({self.type!r}, {self.lexeme!r}, {self.literal!r})'
