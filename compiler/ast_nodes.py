"""
Compact AST node representation for ELIN.

Instead of 30+ individual dataclasses, we use a single generic Node class
with a type string and a fields dict. This cuts ast_nodes.py from ~260 lines
to ~30 lines while keeping the same semantics.

Old:  AllocNode(size=expr)     →  node.type == "alloc", node.fields["size"]
New:  Node("alloc", {"size": expr})
"""

from dataclasses import dataclass, field


@dataclass
class Node:
    """Generic AST node. type is a string like 'assign', 'print', 'alloc'.
    Fields are stored in a dict — access them as node.fields['name']."""
    type: str = ""
    fields: dict = field(default_factory=dict)


# Shorthand so the parser can write N("alloc", size=expr) instead of
# Node("alloc", {"size": expr}) — cleaner and less error-prone.
class N(Node):
    """Shorthand constructor: N("type", key=val, ...) builds Node("type", {key: val})."""
    def __init__(self, node_type: str, **kwargs):
        super().__init__(type=node_type, fields=kwargs)


# Node type constants — makes code self-documenting
REGION_ENTER = "region_enter"
REGION_EXIT = "region_exit"
SEG_USED = "seg_used"
