"""
AST Node definitions for the ELIN compiler.
Each class represents a unique structural element of the ELIN language.
"""

class Node:
    """Base class for all Abstract Syntax Tree nodes."""
    pass

class ProgramNode(Node):
    """The root node of every ELIN program, containing a list of statements."""
    def __init__(self, statements):
        self.statements = statements

class AssignNode(Node):
    """Represents a 'let' assignment: let <type> <name> = <value>."""
    def __init__(self, type_name, name, value):
        self.type_name = type_name  # The declared type (e.g. 'int')
        self.name = name  # The variable name (string)
        self.value = value  # The expression node being assigned

class ReassignNode(Node):
    """Represents updating an existing variable: <name> = <value>."""
    def __init__(self, name, value):
        self.name = name  # The variable name
        self.value = value  # The new expression

class PrintNode(Node):
    """Represents a 'print' statement: print <value_node>."""
    def __init__(self, value_node):
        self.value_node = value_node  # The node (variable or literal) to print

class IfNode(Node):
    """Represents an 'if-else' block with conditions and nested bodies."""
    def __init__(self, condition, body, else_body):
        self.condition = condition  # ConditionNode
        self.body = body  # List of statement nodes for 'if' block
        self.else_body = else_body  # List of statement nodes for 'else' block (can be empty)

class WhileNode(Node):
    """Represents a 'while...wend' loop."""
    def __init__(self, condition, body):
        self.condition = condition  # ConditionNode
        self.body = body  # List of statement nodes for the loop body

class HaltNode(Node):
    """Represents the 'halt' instruction to stop execution."""
    pass

class NumberNode(Node):
    """A literal numeric value in the source code."""
    def __init__(self, value):
        self.value = value  # The raw number string

class StringNode(Node):
    """A literal string value in the source code."""
    def __init__(self, value):
        self.value = value  # The raw string content

class VariableNode(Node):
    """A reference to a variable name."""
    def __init__(self, name):
        self.name = name  # The variable identifier string

class BinaryOpNode(Node):
    """A mathematical operation involving two nodes: <left> <op> <right>."""
    def __init__(self, op, left, right):
        self.op = op  # '+', '-', '*', or '/'
        self.left = left  # Left operand node
        self.right = right  # Right operand node

class ConditionNode(Node):
    """A comparison operation: <left> <op> <right>."""
    def __init__(self, op, left, right):
        self.op = op  # '==', '<', '>', etc.
        self.left = left  # Left operand node
        self.right = right  # Right operand node
