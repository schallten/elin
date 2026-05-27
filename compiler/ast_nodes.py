from dataclasses import dataclass, field


@dataclass
class ProgramNode:
    statements: list = field(default_factory=list)


@dataclass
class AssignNode:
    type_name: str = ""
    name: str = ""
    value: object = None


@dataclass
class ReassignNode:
    name: str = ""
    value: object = None


@dataclass
class PrintNode:
    value_node: object = None


@dataclass
class IfNode:
    condition: object = None
    body: list = field(default_factory=list)
    else_body: list = field(default_factory=list)


@dataclass
class WhileNode:
    condition: object = None
    body: list = field(default_factory=list)


@dataclass
class HaltNode:
    pass


@dataclass
class NumberNode:
    value: str = ""


@dataclass
class StringNode:
    value: str = ""


@dataclass
class VariableNode:
    name: str = ""


@dataclass
class BinaryOpNode:
    op: str = ""
    left: object = None
    right: object = None


@dataclass
class ConditionNode:
    op: str = ""
    left: object = None
    right: object = None


@dataclass
class ArrayNode:
    elements: list = field(default_factory=list)


@dataclass
class ArrayAccessNode:
    name: str = ""
    index: object = None


@dataclass
class ArrayAssignNode:
    name: str = ""
    index: object = None
    value: object = None


@dataclass
class ArrayLenNode:
    name: str = ""


@dataclass
class FunctionDefNode:
    ret_type: str = ""
    name: str = ""
    params: list = field(default_factory=list)
    body: list = field(default_factory=list)


@dataclass
class FunctionCallNode:
    name: str = ""
    args: list = field(default_factory=list)


@dataclass
class UnaryOpNode:
    op: str = ""
    operand: object = None


@dataclass
class AbsNode:
    value: object = None


@dataclass
class InputNode:
    pass


@dataclass
class ReturnNode:
    value: object = None
