from lexer import TokenType, Token

class ASTNode: pass
class ImportNode(ASTNode):
    def __init__(self, module_name): self.module_name = module_name
class NumberNode(ASTNode):
    def __init__(self, value): self.value = value
class StringNode(ASTNode):
    def __init__(self, value): self.value = value
class BooleanNode(ASTNode):
    def __init__(self, value): self.value = value
class VariableNode(ASTNode):
    def __init__(self, name): self.name = name
class BinOpNode(ASTNode):
    def __init__(self, left, op_token, right):
        self.left = left; self.op_token = op_token; self.right = right
class AssignNode(ASTNode):
    def __init__(self, var_node, expr_node):
        self.var_node = var_node; self.expr_node = expr_node
class PrintNode(ASTNode):
    def __init__(self, expr_node): self.expr_node = expr_node
class IfNode(ASTNode):
    def __init__(self, condition, then_block):
        self.condition = condition; self.then_block = then_block
class WhileNode(ASTNode):
    def __init__(self, condition, block):
        self.condition = condition; self.block = block
class BlockNode(ASTNode):
    def __init__(self, statements): self.statements = statements
class FunctionDeclNode(ASTNode):
    def __init__(self, name, params, param_types, body):
        self.name = name; self.params = params; self.param_types = param_types; self.body = body
class ReturnNode(ASTNode):
    def __init__(self, expr_node): self.expr_node = expr_node
class CallNode(ASTNode):
    def __init__(self, func_name, args):
        self.func_name = func_name; self.args = args
class ArrayNode(ASTNode):
    def __init__(self, elements): self.elements = elements
class ArrayIndexNode(ASTNode):
    def __init__(self, array_expr, index_expr):
        self.array_expr = array_expr; self.index_expr = index_expr

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def error(self, message="Invalid Syntax Layout"):
        raise SyntaxError(f"[Line {self.lexer.line}]: Compiling Error - {message} (Unexpected token: '{self.current_token.value}', Type: {self.current_token.type.name})")

    def consume(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error(f"Expected token sequence match error. Expected: '{token_type.value}'")

    def factor(self):
        token = self.current_token
        if token.type == TokenType.NUMBER:
            self.consume(TokenType.NUMBER); return NumberNode(token.value)
        elif token.type == TokenType.STRING:
            self.consume(TokenType.STRING); return StringNode(token.value)
        elif token.type == TokenType.BOOLEAN:
            self.consume(TokenType.BOOLEAN); return BooleanNode(token.value)
        elif token.type == TokenType.LBRACK:
            self.consume(TokenType.LBRACK)
            elements = []
            if self.current_token.type != TokenType.RBRACK:
                elements.append(self.expr())
                while self.current_token.type == TokenType.COMMA:
                    self.consume(TokenType.COMMA); elements.append(self.expr())
            self.consume(TokenType.RBRACK); return ArrayNode(elements)
        elif token.type == TokenType.IDENTIFIER:
            func_name = token.value
            self.consume(TokenType.IDENTIFIER)
            if self.current_token.type == TokenType.LPAREN:
                self.consume(TokenType.LPAREN)
                args = []
                if self.current_token.type != TokenType.RPAREN:
                    args.append(self.expr())
                    while self.current_token.type == TokenType.COMMA:
                        self.consume(TokenType.COMMA); args.append(self.expr())
                self.consume(TokenType.RPAREN); return CallNode(func_name, args)
            base_node = VariableNode(func_name)
            if self.current_token.type == TokenType.LBRACK:
                self.consume(TokenType.LBRACK); idx_expr = self.expr(); self.consume(TokenType.RBRACK); return ArrayIndexNode(base_node, idx_expr)
            return base_node
        elif token.type == TokenType.LPAREN:
            self.consume(TokenType.LPAREN); node = self.expr(); self.consume(TokenType.RPAREN); return node
        self.error("Expected literal value, identifier variable name, array bracket definition, or open parenthesis '('")

    def term(self):
        node = self.factor()
        while self.current_token.type in (TokenType.MAIN_MUL, TokenType.DIV):
            op_token = self.current_token
            if op_token.type == TokenType.MAIN_MUL: self.consume(TokenType.MAIN_MUL)
            elif op_token.type == TokenType.DIV: self.consume(TokenType.DIV)
            node = BinOpNode(node, op_token, self.factor())
        return node

    def arithmetic_expr(self):
        node = self.term()
        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            op_token = self.current_token
            if op_token.type == TokenType.PLUS: self.consume(TokenType.PLUS)
            elif op_token.type == TokenType.MINUS: self.consume(TokenType.MINUS)
            node = BinOpNode(node, op_token, self.term())
        return node

    def comparison_expr(self):
        node = self.arithmetic_expr()
        while self.current_token.type in (TokenType.LT, TokenType.GT, TokenType.EQ):
            op_token = self.current_token
            if op_token.type == TokenType.LT: self.consume(TokenType.LT)
            elif op_token.type == TokenType.GT: self.consume(TokenType.GT)
            elif op_token.type == TokenType.EQ: self.consume(TokenType.EQ)
            node = BinOpNode(node, op_token, self.arithmetic_expr())
        return node

    def expr(self):
        node = self.comparison_expr()
        while self.current_token.type in (TokenType.AND, TokenType.OR):
            op_token = self.current_token
            if op_token.type == TokenType.AND: self.consume(TokenType.AND)
            elif op_token.type == TokenType.OR: self.consume(TokenType.OR)
            node = BinOpNode(node, op_token, self.comparison_expr())
        return node

    def parse_block(self):
        self.consume(TokenType.LBRACE)
        statements = []
        while self.current_token.type != TokenType.RBRACE and self.current_token.type != TokenType.EOF:
            statements.append(self.statement())
        self.consume(TokenType.RBRACE); return BlockNode(statements)

    def function_declaration(self):
        self.consume(TokenType.FN)
        func_name = self.current_token.value
        self.consume(TokenType.IDENTIFIER); self.consume(TokenType.LPAREN)
        params = []
        param_types = {}
        
        if self.current_token.type == TokenType.IDENTIFIER:
            p_name = self.current_token.value
            self.consume(TokenType.IDENTIFIER)
            
            if self.current_token.type == TokenType.LBRACK:
                self.consume(TokenType.LBRACK); self.consume(TokenType.RBRACK)
                param_types[p_name] = "array"
            else:
                param_types[p_name] = "scalar"
                
            params.append(p_name)
            
            while self.current_token.type == TokenType.COMMA:
                self.consume(TokenType.COMMA)
                p_name = self.current_token.value
                self.consume(TokenType.IDENTIFIER)
                
                if self.current_token.type == TokenType.LBRACK:
                    self.consume(TokenType.LBRACK); self.consume(TokenType.RBRACK)
                    param_types[p_name] = "array"
                else:
                    param_types[p_name] = "scalar"
                    
                params.append(p_name)
                
        self.consume(TokenType.RPAREN)
        body_node = self.parse_block()
        return FunctionDeclNode(func_name, params, param_types, body_node)

    def statement(self):
        if self.current_token.type == TokenType.IMPORT:
            self.consume(TokenType.IMPORT)
            module_name = self.current_token.value
            self.consume(TokenType.IDENTIFIER); self.consume(TokenType.SEMICOLON)
            return ImportNode(module_name)
            
        if self.current_token.type == TokenType.FN:
            return self.function_declaration()
        
        if self.current_token.type == TokenType.LET:
            self.consume(TokenType.LET)
            var_name = self.current_token.value
            self.consume(TokenType.IDENTIFIER)
            if self.current_token.type == TokenType.LBRACK:
                self.consume(TokenType.LBRACK); idx_expr = self.expr(); self.consume(TokenType.RBRACK)
                var_node = ArrayIndexNode(VariableNode(var_name), idx_expr)
            else:
                var_node = VariableNode(var_name)
            self.consume(TokenType.ASSIGN); expr_node = self.expr(); self.consume(TokenType.SEMICOLON); return AssignNode(var_node, expr_node)
            
        elif self.current_token.type == TokenType.IDENTIFIER:
            var_name = self.current_token.value
            next_t = self.lexer.peek_next_token()
            
            # FIXED TOKEN LOOKAHEAD COMPILER PASS: Safely route re-assignments
            if next_t.type == TokenType.ASSIGN:
                self.consume(TokenType.IDENTIFIER)
                self.consume(TokenType.ASSIGN)
                expr_node = self.expr()
                self.consume(TokenType.SEMICOLON)
                return AssignNode(VariableNode(var_name), expr_node)
            
            # Route mutations to indices: array[idx] = val;
            elif next_t.type == TokenType.LBRACK:
                self.consume(TokenType.IDENTIFIER)
                self.consume(TokenType.LBRACK)
                idx_expr = self.expr()
                self.consume(TokenType.RBRACK)
                self.consume(TokenType.ASSIGN)
                expr_node = self.expr()
                self.consume(TokenType.SEMICOLON)
                return AssignNode(ArrayIndexNode(VariableNode(var_name), idx_expr), expr_node)
                
            else:
                expr_node = self.expr()
                self.consume(TokenType.SEMICOLON)
                return expr_node
                
        elif self.current_token.type == TokenType.PRINT:
            self.consume(TokenType.PRINT); expr_node = self.expr(); self.consume(TokenType.SEMICOLON); return PrintNode(expr_node)
        elif self.current_token.type == TokenType.IF:
            self.consume(TokenType.IF); self.consume(TokenType.LPAREN); cond = self.expr(); self.consume(TokenType.RPAREN); return IfNode(cond, self.parse_block())
        elif self.current_token.type == TokenType.WHILE:
            self.consume(TokenType.WHILE); self.consume(TokenType.LPAREN); cond = self.expr(); self.consume(TokenType.RPAREN); return WhileNode(cond, self.parse_block())
        elif self.current_token.type == TokenType.RETURN:
            self.consume(TokenType.RETURN)
            expr_node = self.expr() if self.current_token.type != TokenType.SEMICOLON else None
            self.consume(TokenType.SEMICOLON); return ReturnNode(expr_node)
            
        self.error("Unrecognized instruction or syntax layout pattern context statement.")

    def parse(self):
        statements = []
        while self.current_token.type != TokenType.EOF:
            statements.append(self.statement())
        return statements