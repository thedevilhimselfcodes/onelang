import enum

class TokenType(enum.Enum):
    EOF = "EOF"
    NUMBER = "NUMBER"
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"
    IDENTIFIER = "IDENTIFIER"
    
    ASSIGN = "="
    PLUS = "+"
    MINUS = "-"
    MAIN_MUL = "*"
    DIV = "/"
    
    LPAREN = "("
    RPAREN = ")"
    LBRACE = "{"
    RBRACE = "}"
    LBRACK = "["
    RBRACK = "]"
    COMMA = ","
    SEMICOLON = ";"
    
    LT = "<"
    GT = ">"
    EQ = "=="
    AND = "&&"
    OR = "||"
    
    IMPORT = "import"
    LET = "let"
    PRINT = "print"
    IF = "if"
    WHILE = "while"
    FN = "fn"
    RETURN = "return"


class Token:
    def __init__(self, type_token, value):
        self.type = type_token
        self.value = value

    def __repr__(self):
        return f"Token({self.type.name}, {repr(self.value)})"


class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1
        self.current_char = self.text[self.pos] if len(self.text) > 0 else None

    def advance(self):
        self.pos += 1
        if self.pos >= len(self.text):
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            if self.current_char == '\n':
                self.line += 1
            self.advance()

    def skip_comment(self):
        while self.current_char is not None and self.current_char != '\n':
            self.advance()

    def number(self) -> Token:
        result = ""
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '.'):
            result += self.current_char
            self.advance()
        return Token(TokenType.NUMBER, float(result))

    def string(self, quote_type) -> Token:
        result = ""
        self.advance()
        while self.current_char is not None and self.current_char != quote_type:
            result += self.current_char
            self.advance()
        if self.current_char is None:
            raise SyntaxError(f"OneLang Lexer Error: Unterminated string literal on line {self.line}")
        self.advance()
        return Token(TokenType.STRING, result)

    def identifier(self) -> Token:
        result = ""
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()

        keywords = {
            "import": TokenType.IMPORT,
            "let": TokenType.LET,
            "print": TokenType.PRINT,
            "if": TokenType.IF,
            "while": TokenType.WHILE,
            "fn": TokenType.FN,
            "return": TokenType.RETURN,
            "true": TokenType.BOOLEAN,
            "false": TokenType.BOOLEAN
        }
        if result in keywords:
            val_state = True if result == "true" else (False if result == "false" else result)
            return Token(keywords[result], val_state)
        return Token(TokenType.IDENTIFIER, result)

    def peek_next_token(self) -> Token:
        """CRITICAL FIX: Safely scans ahead to return the NEXT token without moving the lexer cursor"""
        saved_pos = self.pos
        saved_line = self.line
        saved_char = self.current_char
        
        # Pull the token following the active processing index
        try:
            token = self.get_next_token()
        finally:
            self.pos = saved_pos
            self.line = saved_line
            self.current_char = saved_char
        return token

    def get_next_token(self) -> Token:
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char == '#':
                self.skip_comment()
                continue

            if self.current_char.isdigit():
                return self.number()

            if self.current_char.isalpha() or self.current_char == '_':
                return self.identifier()

            if self.current_char == '"' or self.current_char == "'":
                return self.string(self.current_char)

            if self.current_char == '&':
                self.advance()
                if self.current_char == '&': self.advance(); return Token(TokenType.AND, "&&")
                raise SyntaxError(f"Lexer Error: Solitary '&' invalid on line {self.line}.")

            if self.current_char == '|':
                self.advance()
                if self.current_char == '|': self.advance(); return Token(TokenType.OR, "||")
                raise SyntaxError(f"Lexer Error: Solitary '|' invalid on line {self.line}.")

            if self.current_char == '=':
                self.advance()
                if self.current_char == '=': self.advance(); return Token(TokenType.EQ, "==")
                return Token(TokenType.ASSIGN, "=")

            if self.current_char == '+': self.advance(); return Token(TokenType.PLUS, "+")
            if self.current_char == '-': self.advance(); return Token(TokenType.MINUS, "-")
            if self.current_char == '*': self.advance(); return Token(TokenType.MAIN_MUL, "*")
            if self.current_char == '/': self.advance(); return Token(TokenType.DIV, "/")
            if self.current_char == '<': self.advance(); return Token(TokenType.LT, "<")
            if self.current_char == '>': self.advance(); return Token(TokenType.GT, ">")
            if self.current_char == '(': self.advance(); return Token(TokenType.LPAREN, "(")
            if self.current_char == ')': self.advance(); return Token(TokenType.RPAREN, ")")
            if self.current_char == '{': self.advance(); return Token(TokenType.LBRACE, "{")
            if self.current_char == '}': self.advance(); return Token(TokenType.RBRACE, "}")
            if self.current_char == '[': self.advance(); return Token(TokenType.LBRACK, "[")
            if self.current_char == ']': self.advance(); return Token(TokenType.RBRACK, "]")
            if self.current_char == ',': self.advance(); return Token(TokenType.COMMA, ",")
            if self.current_char == ';': self.advance(); return Token(TokenType.SEMICOLON, ";")

            raise SyntaxError(f"OneLang Lexer Error: Unknown character '{self.current_char}' on line {self.line}")
        return Token(TokenType.EOF, None)