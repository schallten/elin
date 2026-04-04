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
        index_expr = self.parse_expression(stop_tokens=["RBRACKET"])
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
        cond = self.parse_condition()
        
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
        cond = self.parse_condition()
        
        # Recursively parse the loop body
        body = self.parse_statements()
        
        while self.current() and self.current().type in ["NEWLINE", "SEMI"]:
            self.advance()
            
        self.advance()  # Consumes 'WEND' (or 'END')
        return WhileNode(cond, body)

    def parse_func(self):
        """Parses: func <ret_type> <name> <type1> <arg1> ..."""
        self.advance() # func
        ret_type = self.current().value
        self.advance()
        name = self.current().value
        self.advance()
        
        params = []
        while self.current() and self.current().type not in ["NEWLINE", "SEMI"]:
            p_type = self.current().value
            self.advance()
            p_name = self.current().value
            self.advance()
            params.append((p_type, p_name))
            
        body = self.parse_statements()
        
        if self.current() and self.current().type == "END":
            self.advance()
            
        return FunctionDefNode(ret_type, name, params, body)

    def parse_return(self):
        self.advance() # return
        expr = self.parse_expression(stop_tokens=["NEWLINE", "SEMI"])
        return ReturnNode(expr)

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

    def parse_expression(self, stop_tokens=["NEWLINE", "SEMI"]):
        """
        Encapsulates array access (name[idx]) and then builds a BinaryOp tree.
        """
        if self.current().type == "LBRACKET":
            return self.parse_array_literal()
            
        if self.current().type == "LEN":
            self.advance() # len
            self.advance() # (
            name_tok = self.current()
            self.advance() # name
            self.advance() # )
            return ArrayLenNode(name_tok.value)

        # Slurp tokens until a stop token
        raw_tokens = []
        while self.current() and self.current().type not in stop_tokens:
            raw_tokens.append(self.current())
            self.advance()
            
        if not raw_tokens:
            return None

        # Build a list of 'nodes' (NumberNode, VariableNode, ArrayAccessNode) and 'operator strings'
        prepared_tokens = []
        i = 0
        while i < len(raw_tokens):
            tok = raw_tokens[i]
            # Check for array access: name [ index ]
            if tok.type == "IDENTIFIER" and i + 1 < len(raw_tokens) and raw_tokens[i + 1].type == "LBRACKET":
                # Find the closing RBRACKET
                name = tok.value
                i += 2 # Consume identifier and [
                # For simplicity, we assume index is a single token here for now
                index_tok = raw_tokens[i]
                i += 1 
                if i < len(raw_tokens) and raw_tokens[i].type == "RBRACKET":
                    i += 1
                
                idx_node = NumberNode(index_tok.value) if index_tok.type == "NUMBER" else VariableNode(index_tok.value)
                prepared_tokens.append(ArrayAccessNode(name, idx_node))
            elif tok.type == "NUMBER":
                prepared_tokens.append(NumberNode(tok.value))
                i += 1
            elif tok.type == "STRING":
                prepared_tokens.append(StringNode(tok.value))
                i += 1
            elif tok.type == "IDENTIFIER":
                prepared_tokens.append(VariableNode(tok.value))
                i += 1
            elif tok.type in ["OP", "CMP"]:
                prepared_tokens.append(tok.value)
                i += 1
            else:
                prepared_tokens.append(tok.value)
                i += 1

        # Check for simple comparisons (hack to maintain lookandfeel of original parser)
        for idx, item in enumerate(prepared_tokens):
            if isinstance(item, str) and item in CMP_OPERATORS:
                return ConditionNode(item, prepared_tokens[0], prepared_tokens[2])
                
        # Handle single values
        if len(prepared_tokens) == 1:
            return prepared_tokens[0]
            
        # Use our updated tree builder that handles nodes
        return build_expr_tree_from_nodes(prepared_tokens)

    def parse_array_literal(self):
        """Parses: [val1, val2, ...]."""
        self.advance() # [
        elements = []
        while self.current() and self.current().type != "RBRACKET":
            # For now, only simple literals or variables in arrays
            tok = self.current()
            if tok.type == "NUMBER":
                elements.append(NumberNode(tok.value))
            elif tok.type == "STRING":
                elements.append(StringNode(tok.value))
            elif tok.type == "IDENTIFIER":
                elements.append(VariableNode(tok.value))
            self.advance()
            if self.current() and self.current().type == "COMMA":
                self.advance()
        if self.current() and self.current().type == "RBRACKET":
            self.advance()
        return ArrayNode(elements)

# Helper function moved here to keep Parser class clean
def build_expr_tree(tokens):
    """Temporary tree builder for math expressions (backwards compatibility)."""
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
            if isinstance(t, str) and (t.isdigit() or (t.startswith("-") and t[1:].isdigit())):
                stack.append(NumberNode(t))
            else:
                stack.append(VariableNode(t))
    return stack[0]

def build_expr_tree_from_nodes(nodes_and_ops):
    """Better tree builder that works with already parsed nodes."""
    from expression_parser import infix_to_postfix
    # Convert nodes to a unique string mapping so the postfix converter can handle them
    raw = []
    node_map = {}
    for i, item in enumerate(nodes_and_ops):
        if isinstance(item, str):
            raw.append(item)
        else:
            key = f"__NODE_{i}__"
            node_map[key] = item
            raw.append(key)
            
    postfix = infix_to_postfix(raw)
    
    stack = []
    supported_operators = ["+", "-", "*", "/"]
    for t in postfix:
        if t in supported_operators:
            right = stack.pop()
            left = stack.pop()
            stack.append(BinaryOpNode(t, left, right))
        else:
            if t in node_map:
                stack.append(node_map[t])
            elif isinstance(t, str) and (t.isdigit() or (t.startswith("-") and t[1:].isdigit())):
                stack.append(NumberNode(t))
            else:
                stack.append(VariableNode(t))
                
    # If the stack has multiple items left, it is likely a function call
    if len(stack) > 1 and isinstance(stack[0], VariableNode):
        return FunctionCallNode(stack[0].name, stack[1:])
        
    return stack[0]
