from ast_nodes import *
# We temporarily refer to a helper to convert infix expressions or handle it natively
from ops import CMP_OPERATORS

class Parser:
    """
    The Parser takes a list of tokens from the Lexer and constructs
    an Abstract Syntax Tree (AST) following the ELIN grammar rules.
    """
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        """Returns the token at the current position without advancing."""
        if self.pos < len(self.tokens): 
            return self.tokens[self.pos]
        return None

    def advance(self):
        """Moves the pointer forward by one token."""
        self.pos += 1

    def parse(self):
        """Main entry: parses the tokens into a full ProgramNode."""
        statements = self.parse_statements(root=True)
        return ProgramNode(statements)

    def parse_statements(self, root=False):
        """
        Parses a sequence of statements until a closing keyword or end of tokens.
        Recursive: can be called for nested blocks (if/while).
        """
        stmts = []
        while self.current():
            # Skip empty line tokens or semicolons
            if self.current().type in ["NEWLINE", "SEMI"]:
                self.advance()
                continue
            
            # Stop if we hit a block termination keyword (we don't consume it here)
            if not root and self.current().type in ["END", "ELSE", "WEND"]:
                break
            
            tok = self.current()
            if tok.type == "LET":
                stmts.append(self.parse_let())
            elif tok.type == "PRINT":
                stmts.append(self.parse_print())
            elif tok.type == "IF":
                stmts.append(self.parse_if())
            elif tok.type == "WHILE":
                stmts.append(self.parse_while())
            elif tok.type == "FUNC":
                stmts.append(self.parse_func())
            elif tok.type == "RETURN":
                stmts.append(self.parse_return())
            elif tok.type == "HALT":
                self.advance()
                stmts.append(HaltNode())
            elif tok.type == "IDENTIFIER" and self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type == "LBRACKET":
                stmts.append(self.parse_array_assign())
            elif tok.type == "IDENTIFIER" and self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type == "EQUALS":
                stmts.append(self.parse_reassign())
            elif tok.type in ["IDENTIFIER", "LPAREN", "LBRACKET", "NUMBER", "STRING", "LEN"]:
                stmts.append(self.parse_expression())
            elif tok.type in ["COMMA", "RPAREN", "RBRACKET"]:
                self.advance()
            else:
                raise Exception(f"Syntax error at {tok.type}: unexpected token")
        return stmts

    def parse_reassign(self):
        """Parses: <var> = <expression>."""
        name_tok = self.current()
        self.advance()  # Consumes identifier
        self.advance()  # Consumes '='
        expr = self.parse_expression()
        return ReassignNode(name_tok.value, expr)

    def parse_array_assign(self):
        """Parses: <var>[index] = <expression>."""
        name_tok = self.current()
        self.advance() # identifier
        self.advance() # [
        index_expr = self.parse_expression()
        if self.current().type == "RBRACKET":
            self.advance()
        if self.current().type == "EQUALS":
            self.advance()
        value_expr = self.parse_expression()
        return ArrayAssignNode(name_tok.value, index_expr, value_expr)


    def parse_let(self):
        """Parses: let [arr] <type> <var> = <expression>."""
        self.advance()  # Consumes 'LET'
        
        is_array = False
        if self.current().type == "ARR":
            is_array = True
            self.advance()
            
        type_tok = self.current()
        self.advance()  # Consumes type (int, str)
        name_tok = self.current()
        self.advance()  # Consumes identifier
        self.advance()  # Consumes '='
        expr = self.parse_expression()
        
        full_type = f"arr {type_tok.value}" if is_array else type_tok.value
        return AssignNode(full_type, name_tok.value, expr)

    def parse_print(self):
        """Parses: print <value>."""
        self.advance()  # Consumes 'PRINT'
        expr = self.parse_expression()
        return PrintNode(expr)

    def parse_if(self):
        """Parses: if <condition> ... [else ...] end."""
        self.advance()  # Consumes 'IF'
        cond = self.parse_expression()
        
        # Recursively parse the 'then' body
        body = self.parse_statements()
        
        else_body = []
        # Consume any trailing newlines before checking for ELSE
        while self.current() and self.current().type in ["NEWLINE", "SEMI"]:
            self.advance()
            
        if self.current() and self.current().type == "ELSE":
            self.advance()  # Consumes 'ELSE'
            # Recursively parse the 'else' body
            else_body = self.parse_statements()
        
        while self.current() and self.current().type in ["NEWLINE", "SEMI"]:
            self.advance()
            
        self.advance()  # Consumes 'END'
        return IfNode(cond, body, else_body)

    def parse_while(self):
        """Parses: while <condition> ... wend."""
        self.advance()  # Consumes 'WHILE'
        cond = self.parse_expression()
        
        # Recursively parse the loop body
        body = self.parse_statements()
        
        while self.current() and self.current().type in ["NEWLINE", "SEMI"]:
            self.advance()
            
        self.advance()  # Consumes 'WEND' (or 'END')
        return WhileNode(cond, body)

    def parse_func(self):
        """Parses: func <ret_type> <name> [arr] <type1> <arg1> ..."""
        self.advance() # func
        ret_type = self.current().value
        self.advance()
        name = self.current().value
        self.advance()
        
        params = []
        while self.current() and self.current().type not in ["NEWLINE", "SEMI"]:
            p_is_arr = False
            if self.current().type == "ARR":
                p_is_arr = True
                self.advance()
                
            p_type = self.current().value
            self.advance()
            p_name = self.current().value
            self.advance()
            
            full_type = f"arr {p_type}" if p_is_arr else p_type
            params.append((full_type, p_name))
            
        body = self.parse_statements()
        
        if self.current() and self.current().type == "END":
            self.advance()
            
        return FunctionDefNode(ret_type, name, params, body)

    def parse_return(self):
        self.advance() # return
        expr = self.parse_expression()
        return ReturnNode(expr)

    def get_precedence(self, op_type, op_val):
        if op_type in ["COMMA", "RPAREN", "RBRACKET", "SEMI", "NEWLINE"]:
            return -1
        if op_val in CMP_OPERATORS:
            return 1
        if op_val in ["+", "-"]:
            return 2
        if op_val in ["*", "/"]:
            return 3
        return 0

    def parse_expression(self, precedence=0):
        """
        Direct AST-building Pratt parser for expressions.
        Handles math, comparisons, and function calls.
        """
        left = self.parse_primary()
        
        while True:
            curr = self.current()
            if not curr: break
            
            # Use get_precedence to check if we should continue
            op_prec = self.get_precedence(curr.type, curr.value)
            if op_prec < 0: # Explicit stop tokens
                break
                
            # 1. Infix operators (math, comparison)
            if curr.type in ["OP", "CMP"]:
                if op_prec <= precedence:
                    break
                
                self.advance()
                right = self.parse_expression(op_prec)
                if curr.value in CMP_OPERATORS:
                    left = ConditionNode(curr.value, left, right)
                else:
                    left = BinaryOpNode(curr.value, left, right)
                continue
            
            # 2. Function calls (comma-separated with parens, or space-separated)
            if curr.type == "LPAREN":
                if isinstance(left, VariableNode):
                    func_name = left.name
                    self.advance() # (
                    args = []
                    while self.current() and self.current().type != "RPAREN":
                        args.append(self.parse_expression())
                        if self.current() and self.current().type == "COMMA":
                            self.advance()
                    if self.current() and self.current().type == "RPAREN":
                        self.advance() # )
                    left = FunctionCallNode(func_name, args)
                    continue
            
            # Legacy/Alternative space-separated function calls
            if precedence == 0 and curr.type in ["NUMBER", "STRING", "IDENTIFIER", "LPAREN", "LBRACKET", "LEN"]:
                # Convert VariableNode to FunctionCallNode if it's the first argument
                if isinstance(left, VariableNode):
                    left = FunctionCallNode(left.name, [])
                
                if isinstance(left, FunctionCallNode):
                    # Parse next argument with higher precedence so it doesn't slurp the rest of the call
                    arg = self.parse_expression(precedence=10) 
                    left.args.append(arg)
                    continue
            
            break
            
        return left

    def parse_primary(self):
        """Parses literal values, variables, and grouped expressions."""
        tok = self.current()
        if not tok:
            raise Exception("Unexpected end of input")
            
        if tok.type == "NUMBER":
            self.advance()
            return NumberNode(tok.value)
        elif tok.type == "STRING":
            self.advance()
            return StringNode(tok.value)
        elif tok.type == "IDENTIFIER":
            name = tok.value
            self.advance()
            # Array access check
            if self.current() and self.current().type == "LBRACKET":
                self.advance() # [
                idx = self.parse_expression()
                if self.current() and self.current().type == "RBRACKET":
                    self.advance() # ]
                return ArrayAccessNode(name, idx)
            return VariableNode(name)
        elif tok.type == "LBRACKET":
            return self.parse_array_literal()
        elif tok.type == "LPAREN":
            self.advance() # (
            expr = self.parse_expression()
            if self.current() and self.current().type == "RPAREN":
                self.advance() # )
            return expr
        elif tok.type == "LEN":
            self.advance() # len
            self.advance() # (
            name_tok = self.current()
            self.advance() # identifier
            self.advance() # )
            return ArrayLenNode(name_tok.value)
        
        raise Exception(f"Unexpected token in expression: {tok.type}")

    def parse_array_literal(self):
        """Parses: [val1, val2, ...]."""
        self.advance() # [
        elements = []
        while self.current() and self.current().type != "RBRACKET":
            elements.append(self.parse_expression())
            if self.current() and self.current().type == "COMMA":
                self.advance()
        if self.current() and self.current().type == "RBRACKET":
            self.advance()
        return ArrayNode(elements)

