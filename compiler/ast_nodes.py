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

class ArrayNode(Node):
    """Represents a literal array: [val1, val2, ...]."""
    def __init__(self, elements):
        self.elements = elements  # List of expression nodes

class ArrayAccessNode(Node):
    """Represents accessing an array element: name[index]."""
    def __init__(self, name, index):
        self.name = name  # The array variable name
        self.index = index  # The expression node for the index

class ArrayAssignNode(Node):
    """Represents setting an array element: name[index] = value."""
    def __init__(self, name, index, value):
        self.name = name
        self.index = index
        self.value = value

class ArrayLenNode(Node):
    """Represents the length of an array: len(name)."""
    def __init__(self, name):
        self.name = name

class FunctionDefNode(Node):
    """Represents a function definition: func <ret_type> <name> <params...> ... end."""
    def __init__(self, ret_type, name, params, body):
        self.ret_type = ret_type
        self.name = name
        self.params = params  # List of tuples (type, name)
        self.body = body  # List of statements

class FunctionCallNode(Node):
    """Represents calling a function: name(arg1, arg2...)"""
    def __init__(self, name, args):
        self.name = name
        self.args = args

class ReturnNode(Node):
    """Represents a return statement: return <val>."""
    def __init__(self, value):
        self.value = value
