from ast_nodes import *
# We temporarily refer to a helper to convert infix expressions or handle it natively
from ops import OP_MAP, CMP_OPERATORS

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
            # Skip empty line tokens
            if self.current().type == "NEWLINE":
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
            elif tok.type == "HALT":
                self.advance()
                stmts.append(HaltNode())
            elif tok.type == "IDENTIFIER" and self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type == "EQUALS":
                stmts.append(self.parse_reassign())
            else:
                raise Exception(f"Syntax error: unexpected token {tok.type}")
        return stmts

    def parse_reassign(self):
        """Parses: <var> = <expression>."""
        name_tok = self.current()
        self.advance()  # Consumes identifier
        self.advance()  # Consumes '='
        expr = self.parse_expression()
        return ReassignNode(name_tok.value, expr)


    def parse_let(self):
        """Parses: let <type> <var> = <expression>."""
        self.advance()  # Consumes 'LET'
        type_tok = self.current()
        self.advance()  # Consumes type (int, str)
        name_tok = self.current()
        self.advance()  # Consumes identifier
        self.advance()  # Consumes '='
        expr = self.parse_expression()
        return AssignNode(type_tok.value, name_tok.value, expr)

    def parse_print(self):
        """Parses: print <value>."""
        self.advance()  # Consumes 'PRINT'
        val_tok = self.current()
        self.advance()
        if val_tok.type == "NUMBER":
            return PrintNode(NumberNode(val_tok.value))
        elif val_tok.type == "STRING":
            return PrintNode(StringNode(val_tok.value))
        else:
            return PrintNode(VariableNode(val_tok.value))

    def parse_if(self):
        """Parses: if <condition> ... [else ...] end."""
        self.advance()  # Consumes 'IF'
        cond = self.parse_condition()
        
        # Recursively parse the 'then' body
        body = self.parse_statements()
        
        else_body = []
        # Consume any trailing newlines before checking for ELSE
        while self.current() and self.current().type == "NEWLINE":
            self.advance()
            
        if self.current() and self.current().type == "ELSE":
            self.advance()  # Consumes 'ELSE'
            # Recursively parse the 'else' body
            else_body = self.parse_statements()
        
        while self.current() and self.current().type == "NEWLINE":
            self.advance()
            
        self.advance()  # Consumes 'END'
        return IfNode(cond, body, else_body)

    def parse_while(self):
        """Parses: while <condition> ... wend."""
        self.advance()  # Consumes 'WHILE'
        cond = self.parse_condition()
        
        # Recursively parse the loop body
        body = self.parse_statements()
        
        while self.current() and self.current().type == "NEWLINE":
            self.advance()
            
        self.advance()  # Consumes 'WEND'
        return WhileNode(cond, body)

    def parse_condition(self):
        """Parses a simple comparison: <expr> <op> <expr>."""
        left_tok = self.current()
        self.advance()
        op_tok = self.current()
        self.advance()
        right_tok = self.current()
        self.advance()
        
        left_node = NumberNode(left_tok.value) if left_tok.type == "NUMBER" else VariableNode(left_tok.value)
        right_node = NumberNode(right_tok.value) if right_tok.type == "NUMBER" else VariableNode(right_tok.value)
        return ConditionNode(op_tok.value, left_node, right_node)

    def parse_expression(self):
        """
        Parses math expressions or comparisons.
        Converts tokens to localized tree structures (BinaryOpNode).
        """
        expr_tokens = []
        while self.current() and self.current().type != "NEWLINE":
            expr_tokens.append(self.current())
            self.advance()
            
        if not expr_tokens:
            return None
            
        # Quick check for simple comparisons like x = a > b
        for i, t in enumerate(expr_tokens):
            if t.type == "CMP":
                op = t.value
                left_tok = expr_tokens[0]
                right_tok = expr_tokens[2]
                left_node = NumberNode(left_tok.value) if left_tok.type == "NUMBER" else VariableNode(left_tok.value)
                right_node = NumberNode(right_tok.value) if right_tok.type == "NUMBER" else VariableNode(right_tok.value)
                return ConditionNode(op, left_node, right_node)
                
        # Handle single values
        if len(expr_tokens) == 1:
            tok = expr_tokens[0]
            if tok.type == "NUMBER": return NumberNode(tok.value)
            if tok.type == "STRING": return StringNode(tok.value)
            return VariableNode(tok.value)
            
        # Handle complex math by converting to postfix then building a tree
        # (Internal logic uses Shunting Yard to build AST)
        return build_expr_tree(expr_tokens)

# Helper function moved here to keep Parser class clean
def build_expr_tree(tokens):
    """Temporary tree builder for math expressions."""
    # Simplified parser: for now we assume simple flat postfix or basic processing
    # In a full AST refactor, we usually use operator precedence climbing.
    # For now, we'll keep the existing logic that works with the stack.
    from expression_parser import infix_to_postfix
    raw = [t.value for t in tokens]
    postfix = infix_to_postfix(raw)
    
    stack = []
    supported_operators = ["+", "-", "*", "/"]
    for t in postfix:
        if t in supported_operators:
            right = stack.pop()
            left = stack.pop()
            stack.append(BinaryOpNode(t, left, right))
        else:
            # Create leaf nodes (ensure t is a string before calling isdigit)
            if isinstance(t, str) and (t.isdigit() or (t.startswith("-") and t[1:].isdigit())):
                stack.append(NumberNode(t))
            else:
                # Fallback for variables or strings already in tree format? 
                # Actually tokens were raw strings from 'raw' list
                stack.append(VariableNode(t))
    return stack[0]
