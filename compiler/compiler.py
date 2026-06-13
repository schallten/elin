import sys
from ops import (
    HALT, PUSH, LOAD, STORE, JMP, JZ, PRINT, PRINT_STR, PUSH_STR,
    OP_MAP, CMP_OP_MAP,
    MAKE_ARR, ARR_GET, ARR_SET, ARR_LEN, PUSH_ARR,
    CALL, RET, LOAD_LOCAL, STORE_LOCAL,
    PUSH_CONST,
    DUP, DROP, SWAP,
    NEG, NOT, NOP, INC, DEC,
    MOD, ABS, INPUT, TRACE,
    READ, WRITE, FLUSH,
    STRLEN, STRCAT, SUBSTR, STRCMP,
    TIME, DELAY, RTC_READ, RTC_WRITE,
    FOPEN, FREAD, FWRITE, FCLOSE,
    RAND, SRAND, CALL_EXTERN,
    ALLOC, FREE, LOAD_H, STORE_H, HEAP_LEN,
    REGION_ENTER, REGION_EXIT, SEG_USED
)
from ast_nodes import Node
from lexer import lex
from parser import parse

# Helper to get a field from a Node, raising a clear error if missing
def f(node, key):
    """Get field `key` from a Node. Shorthand for node.fields[key]."""
    return node.fields[key]


# ===========================================================================
# Type Inference
# ===========================================================================

# Nodes that always return a fixed type — no inspection needed
FIXED_TYPES = {
    "number": "int", "condition": "int", "array_len": "int", "abs": "int",
    "input": "int", "write": "int", "flush": "int", "strlen": "int",
    "strcmp": "int", "time": "int", "delay": "int", "rtc_read": "int",
    "rtc_write": "int", "fopen": "int", "fwrite": "int", "fclose": "int",
    "rand": "int", "srand": "int", "alloc": "int", "heap_len": "int",
    "load_h": "int",
    "string": "str", "read_str": "str", "strcat": "str", "substr": "str",
    "fread": "str",
    "extern": "void", "free": "void", "store_h": "void",
    "region_enter": "void", "region_exit": "void",
    "seg_used": "int", "alloc_seg": "int",
}


def tc_infer_type(node, env):
    # Fixed-type nodes: just look up the table
    if node.type in FIXED_TYPES:
        return FIXED_TYPES[node.type]

    if node.type == "variable":
        name = f(node, "name")
        loc = env["current_locals"]
        if loc and name in loc:
            return loc[name]
        if name in env["variables"]:
            return env["variables"][name]
        raise Exception(f"Type Error: Variable '{name}' undefined.")

    if node.type == "unary_op":
        t = tc_infer_type(f(node, "operand"), env)
        if t != "int":
            raise Exception(f"Type Error: Unary needs int, got {t}")
        return "int"

    if node.type == "binary_op":
        lt = tc_infer_type(f(node, "left"), env)
        rt = tc_infer_type(f(node, "right"), env)
        if lt != "int" or rt != "int":
            raise Exception(f"Type Error: Math needs int, got {lt}, {rt}")
        return "int"

    if node.type == "array":
        elts = f(node, "elements")
        if not elts:
            return "arr int"
        return f"arr {tc_infer_type(elts[0], env)}"

    if node.type == "array_access":
        name = f(node, "name")
        if isinstance(name, str):
            t = tc_get_var_type(name, env)
        else:
            t = tc_get_var_type(name.fields["name"], env)
        return t.split(" ", 1)[1] if " " in t else "int"

    if node.type == "func_call":
        name = f(node, "name")
        funcs = env["functions"]
        externs = env["externs"]
        if name in funcs:
            return funcs[name]["ret_type"]
        if name in externs:
            return externs[name]["ret_type"]
        raise Exception(f"Type Error: Function '{name}' undefined")

    return "unknown"


def tc_get_var_type(name, env):
    loc = env["current_locals"]
    if loc and name in loc:
        return loc[name]
    if name in env["variables"]:
        return env["variables"][name]
    raise Exception(f"Type Error: Variable '{name}' undefined")


# ===========================================================================
# Type Checker
# ===========================================================================

# Leaf nodes — no children to recurse into
_LEAF_TYPES = frozenset({
    "number", "string", "variable", "array_len", "abs", "input",
    "read_str", "flush", "time", "rand", "srand", "rtc_read",
    "fopen", "fread", "heap_len",
})

# Nodes with a single child to recurse into, mapped to their field name
_VALUE_CHILD = {
    "return": "value", "delay": "value", "write": "value",
    "strlen": "value", "free": "handle", "rtc_write": "value",
    "fclose": "fd", "fread": "fd", "fopen": "path",
}

# Nodes with left/right children
_TWO_CHILD = frozenset({"binary_op", "condition", "strcat", "strcmp"})


def check(ast, env):
    t = ast.type

    if t == "program":
        for s in f(ast, "statements"):
            env = check(s, env)
        return env

    if t == "assign":
        vt = tc_infer_type(f(ast, "value"), env)
        tn = f(ast, "type_name")
        if tn != vt:
            raise Exception(f"Type Error: {vt} -> {tn}")
        target = env["current_locals"] if env["current_locals"] is not None else env["variables"]
        target[f(ast, "name")] = tn
        return check(f(ast, "value"), env)

    if t == "reassign":
        vt = tc_infer_type(f(ast, "value"), env)
        et = tc_get_var_type(f(ast, "name"), env)
        if vt != et:
            raise Exception(f"Type Error: {vt} -> {et}")
        return check(f(ast, "value"), env)

    if t == "if":
        check(f(ast, "condition"), env)
        for s in f(ast, "body"):
            env = check(s, env)
        for s in f(ast, "else_body"):
            env = check(s, env)
        return env

    if t == "while":
        check(f(ast, "condition"), env)
        for s in f(ast, "body"):
            env = check(s, env)
        return env

    if t == "func_def":
        name = f(ast, "name")
        params = f(ast, "params")
        env["functions"][name] = {"ret_type": f(ast, "ret_type"), "params": [pt for pt, _ in params]}
        old = env["current_locals"]
        env["current_locals"] = {pn: pt for pt, pn in params}
        for s in f(ast, "body"):
            env = check(s, env)
        env["current_locals"] = old
        return env

    if t == "func_call":
        name = f(ast, "name")
        args = f(ast, "args")
        if name in env["functions"]:
            info = env["functions"][name]
            if len(args) != len(info["params"]):
                raise Exception(f"Type Error: {name} expects {len(info['params'])} args, got {len(args)}")
            for i, arg in enumerate(args):
                at = tc_infer_type(arg, env)
                if at != info["params"][i]:
                    raise Exception(f"Type Error: Arg {i} {at} -> {info['params'][i]}")
        elif name in env["externs"]:
            for arg in args:
                check(arg, env)
        else:
            raise Exception(f"Type Error: Function '{name}' undefined")
        return env

    if t == "unary_op":
        return check(f(ast, "operand"), env)

    if t == "array_assign":
        check(f(ast, "index"), env)
        return check(f(ast, "value"), env)

    if t == "substr":
        check(f(ast, "string"), env)
        check(f(ast, "offset"), env)
        return check(f(ast, "length"), env)

    if t == "store_h":
        check(f(ast, "handle"), env)
        check(f(ast, "index"), env)
        return check(f(ast, "value"), env)

    if t == "load_h":
        check(f(ast, "handle"), env)
        return check(f(ast, "index"), env)

    if t == "fwrite":
        check(f(ast, "fd"), env)
        return check(f(ast, "string"), env)

    if t == "extern":
        env["externs"][f(ast, "func_name")] = {"library": f(ast, "library"), "ret_type": "int"}
        return env

    # Generic handlers by pattern
    if t in _LEAF_TYPES:
        return env
    if t == "print":
        return check(f(ast, "value_node"), env)
    if t in _VALUE_CHILD:
        return check(f(ast, _VALUE_CHILD[t]), env)
    if t in _TWO_CHILD:
        check(f(ast, "left"), env)
        return check(f(ast, "right"), env)

    return env

    if t == "assign":
        vt = tc_infer_type(f(ast, "value"), env)
        tn = f(ast, "type_name")
        if tn != vt:
            raise Exception(f"Type Error: {vt} -> {tn}")
        if env["current_locals"] is not None:
            env["current_locals"][f(ast, "name")] = tn
        else:
            env["variables"][f(ast, "name")] = tn
        return check(f(ast, "value"), env)

    if t == "reassign":
        vt = tc_infer_type(f(ast, "value"), env)
        et = tc_get_var_type(f(ast, "name"), env)
        if vt != et:
            raise Exception(f"Type Error: {vt} -> {et}")
        return check(f(ast, "value"), env)

    if t == "print":
        return check(f(ast, "value_node"), env)

    if t == "if":
        check(f(ast, "condition"), env)
        for s in f(ast, "body"):
            env = check(s, env)
        for s in f(ast, "else_body"):
            env = check(s, env)
        return env

    if t == "while":
        check(f(ast, "condition"), env)
        for s in f(ast, "body"):
            env = check(s, env)
        return env

    if t == "func_def":
        rt = f(ast, "ret_type")
        name = f(ast, "name")
        params = f(ast, "params")
        body = f(ast, "body")
        param_types = [pt for pt, pn in params]
        env["functions"][name] = {"ret_type": rt, "params": param_types}
        old = env["current_locals"]
        env["current_locals"] = {pn: pt for pt, pn in params}
        for s in body:
            env = check(s, env)
        env["current_locals"] = old
        return env

    if t == "func_call":
        name = f(ast, "name")
        args = f(ast, "args")
        funcs = env["functions"]
        externs = env["externs"]
        if name in funcs:
            info = funcs[name]
            if len(args) != len(info["params"]):
                raise Exception(
                    f"Type Error: {name} expects {len(info['params'])} args, got {len(args)}"
                )
            for i, arg in enumerate(args):
                at = tc_infer_type(arg, env)
                if at != info["params"][i]:
                    raise Exception(f"Type Error: Arg {i} {at} -> {info['params'][i]}")
        elif name in externs:
            for arg in args:
                check(arg, env)
        else:
            raise Exception(f"Type Error: Function '{name}' undefined")
        return env

    if t in _LEAF_TYPES:
        return env
    if t == "print":
        return check(f(ast, "value_node"), env)
    if t in _VALUE_CHILD:
        return check(f(ast, _VALUE_CHILD[t]), env)
    if t in _TWO_CHILD:
        check(f(ast, "left"), env)
        return check(f(ast, "right"), env)
    if t == "unary_op":
        return check(f(ast, "operand"), env)
    if t == "array_assign":
        check(f(ast, "index"), env)
        return check(f(ast, "value"), env)
    if t == "substr":
        check(f(ast, "string"), env)
        check(f(ast, "offset"), env)
        return check(f(ast, "length"), env)
    if t == "store_h":
        check(f(ast, "handle"), env)
        check(f(ast, "index"), env)
        return check(f(ast, "value"), env)
    if t == "load_h":
        check(f(ast, "handle"), env)
        return check(f(ast, "index"), env)
    if t == "fwrite":
        check(f(ast, "fd"), env)
        return check(f(ast, "string"), env)
    if t in ("region_enter", "region_exit", "seg_used"):
        return check(f(ast, "segment"), env)
    if t == "extern":
        env["externs"][f(ast, "func_name")] = {"library": f(ast, "library"), "ret_type": "int"}
        return env

    return env


# ===========================================================================
# Code Generation
# ===========================================================================

def make_state(package_name):
    return {
        "package_name": package_name,
        "bytecode": [],
        "variables": {},
        "next_available_index": 0,
        "string_pool": [],
        "array_pool": [],
        "constant_pool": [],
        "functions": {},
        "externs": {},
        "current_scope_locals": None,
        "local_next_index": 0,
    }


def cg_register_variable(name, var_type, state):
    if state["current_scope_locals"] is not None:
        idx = state["local_next_index"]
        state["current_scope_locals"][name] = {
            "index": idx, "type": var_type, "is_used": False
        }
        state["local_next_index"] += 1
        return idx, True
    state["variables"][name] = {
        "index": state["next_available_index"],
        "type": var_type,
        "is_used": False,
    }
    idx = state["variables"][name]["index"]
    state["next_available_index"] += 1
    return idx, False


def cg_lookup_variable_index(name, state):
    if state["current_scope_locals"] and name in state["current_scope_locals"]:
        state["current_scope_locals"][name]["is_used"] = True
        return state["current_scope_locals"][name]["index"], True
    state["variables"][name]["is_used"] = True
    return state["variables"][name]["index"], False


def cg_infer_type(node, state):
    if node.type == "string":
        return "str"
    if node.type == "variable":
        name = f(node, "name")
        if state["current_scope_locals"] and name in state["current_scope_locals"]:
            return state["current_scope_locals"][name]["type"]
        return state["variables"][name]["type"]
    if node.type == "func_call":
        name = f(node, "name")
        if name in state["functions"]:
            return state["functions"][name]["ret_type"]
        if name in state["externs"]:
            return state["externs"][name]["ret_type"]
    return "int"


def cg_add_push(val, state):
    pool = state["constant_pool"]
    if val not in pool:
        pool.append(val)
    idx = pool.index(val)
    state["bytecode"].append(f"{PUSH_CONST} {idx}")


def cg_add_push_str(s, state):
    pool = state["string_pool"]
    if s not in pool:
        pool.append(s)
    state["bytecode"].append(f"{PUSH_STR} {pool.index(s)}")


def cg_add_push_arr(vals, state):
    pool = state["array_pool"]
    if vals not in pool:
        pool.append(vals)
    state["bytecode"].append(f"{PUSH_ARR} {pool.index(vals)}")


def cg_add_load(idx, local, state):
    state["bytecode"].append(f"{LOAD_LOCAL if local else LOAD} {idx}")


def cg_add_store(idx, local, state):
    state["bytecode"].append(f"{STORE_LOCAL if local else STORE} {idx}")


def cg_add_operation(op, state):
    state["bytecode"].append(str(op))


def generate(ast, state):
    t = ast.type

    if t == "program":
        for s in f(ast, "statements"):
            state = generate(s, state)
        return state

    if t == "assign":
        idx, local = cg_register_variable(f(ast, "name"), f(ast, "type_name"), state)
        state = generate(f(ast, "value"), state)
        cg_add_store(idx, local, state)
        return state

    if t == "array_assign":
        idx, local = cg_lookup_variable_index(f(ast, "name"), state)
        cg_add_load(idx, local, state)
        state = generate(f(ast, "index"), state)
        state = generate(f(ast, "value"), state)
        cg_add_operation(ARR_SET, state)
        return state

    if t == "reassign":
        name = f(ast, "name")
        val = f(ast, "value")
        # Optimize x = x + 1 -> INC and x = x - 1 -> DEC
        if val.type == "binary_op":
            if (f(val, "left").type == "variable" and f(val, "left").fields["name"] == name
                    and f(val, "right").type == "number" and f(val, "right").fields["value"] == "1"):
                idx, local = cg_lookup_variable_index(name, state)
                if f(val, "op") == "+":
                    cg_add_operation(f"{INC} {idx}", state)
                elif f(val, "op") == "-":
                    cg_add_operation(f"{DEC} {idx}", state)
                return state
        idx, local = cg_lookup_variable_index(name, state)
        state = generate(val, state)
        cg_add_store(idx, local, state)
        return state

    if t == "print":
        vn = f(ast, "value_node")
        state = generate(vn, state)
        cg_add_operation(
            PRINT_STR if cg_infer_type(vn, state) == "str" else PRINT,
            state,
        )
        return state

    if t == "if":
        cond = f(ast, "condition")
        body = f(ast, "body")
        else_body = f(ast, "else_body")
        state = generate(cond, state)
        jz_idx = len(state["bytecode"])
        state["bytecode"].append("JZ_PLACEHOLDER")
        for s in body:
            state = generate(s, state)
        if else_body:
            jmp_idx = len(state["bytecode"])
            state["bytecode"].append("JMP_PLACEHOLDER")
            else_start = len(state["bytecode"])
            state["bytecode"][jz_idx] = f"{JZ} {else_start}"
            for s in else_body:
                state = generate(s, state)
            finish = len(state["bytecode"])
            state["bytecode"][jmp_idx] = f"{JMP} {finish}"
        else:
            state["bytecode"][jz_idx] = f"{JZ} {len(state['bytecode'])}"
        return state

    if t == "while":
        cond = f(ast, "condition")
        body = f(ast, "body")
        start = len(state["bytecode"])
        state = generate(cond, state)
        jz_idx = len(state["bytecode"])
        state["bytecode"].append("JZ_PLACEHOLDER")
        for s in body:
            state = generate(s, state)
        cg_add_operation(f"{JMP} {start}", state)
        state["bytecode"][jz_idx] = f"{JZ} {len(state['bytecode'])}"
        return state

    if t == "halt":
        cg_add_operation(HALT, state)
        return state

    if t == "unary_op":
        op = f(ast, "op")
        oper = f(ast, "operand")
        if oper.type == "number":
            a = int(f(oper, "value"))
            val = -a if op == "-" else (1 if a == 0 else 0)
            cg_add_push(str(val), state)
            return state
        state = generate(oper, state)
        cg_add_operation(NEG if op == "-" else NOT, state)
        return state

    if t == "condition":
        l = f(ast, "left")
        r = f(ast, "right")
        if l.type == "number" and r.type == "number":
            a, b = int(f(l, "value")), int(f(r, "value"))
            op = f(ast, "op")
            if op == "==":   val = 1 if a == b else 0
            elif op == "!=": val = 1 if a != b else 0
            elif op == "<":  val = 1 if a < b else 0
            elif op == "<=": val = 1 if a <= b else 0
            elif op == ">":  val = 1 if a > b else 0
            elif op == ">=": val = 1 if a >= b else 0
            cg_add_push(str(val), state)
            return state
        state = generate(l, state)
        state = generate(r, state)
        cg_add_operation(CMP_OP_MAP[f(ast, "op")], state)
        return state

    if t == "binary_op":
        l = f(ast, "left")
        r = f(ast, "right")
        if l.type == "number" and r.type == "number":
            a, b = int(f(l, "value")), int(f(r, "value"))
            op = f(ast, "op")
            if op == "+": val = a + b
            elif op == "-": val = a - b
            elif op == "*": val = a * b
            elif op == "/": val = a // b if b != 0 else 0
            elif op == "%": val = a % b if b != 0 else 0
            cg_add_push(str(val), state)
            return state
        state = generate(l, state)
        state = generate(r, state)
        cg_add_operation(OP_MAP[f(ast, "op")], state)
        return state

    if t == "number":
        cg_add_push(f(ast, "value"), state)
        return state

    if t == "string":
        cg_add_push_str(f(ast, "value"), state)
        return state

    if t == "variable":
        idx, local = cg_lookup_variable_index(f(ast, "name"), state)
        cg_add_load(idx, local, state)
        return state

    if t == "array":
        elts = f(ast, "elements")
        all_lit = all(e.type in ("number", "string") for e in elts)
        if all_lit:
            vals = []
            for e in elts:
                if e.type == "string":
                    pool = state["string_pool"]
                    if f(e, "value") not in pool:
                        pool.append(f(e, "value"))
                    vals.append(pool.index(f(e, "value")))
                else:
                    vals.append(f(e, "value"))
            cg_add_push_arr(vals, state)
        else:
            for e in elts:
                state = generate(e, state)
            cg_add_operation(f"{MAKE_ARR} {len(elts)}", state)
        return state

    if t == "array_access":
        idx, local = cg_lookup_variable_index(f(ast, "name"), state)
        cg_add_load(idx, local, state)
        state = generate(f(ast, "index"), state)
        cg_add_operation(ARR_GET, state)
        return state

    if t == "array_len":
        name_node = f(ast, "name")
        name = name_node.fields["name"] if name_node.type == "variable" else name_node
        idx, local = cg_lookup_variable_index(name, state)
        cg_add_load(idx, local, state)
        cg_add_operation(ARR_LEN, state)
        return state

    if t == "abs":
        state = generate(f(ast, "value"), state)
        cg_add_operation(ABS, state)
        return state

    if t == "input":
        cg_add_operation(INPUT, state)
        return state

    if t == "read_str":
        cg_add_operation(READ, state)
        return state

    if t == "write":
        state = generate(f(ast, "value"), state)
        cg_add_operation(WRITE, state)
        return state

    if t == "flush":
        cg_add_operation(FLUSH, state)
        return state

    if t == "strlen":
        state = generate(f(ast, "value"), state)
        cg_add_operation(STRLEN, state)
        return state

    if t == "strcat":
        state = generate(f(ast, "left"), state)
        state = generate(f(ast, "right"), state)
        cg_add_operation(STRCAT, state)
        return state

    if t == "substr":
        state = generate(f(ast, "string"), state)
        state = generate(f(ast, "offset"), state)
        state = generate(f(ast, "length"), state)
        cg_add_operation(SUBSTR, state)
        return state

    if t == "strcmp":
        state = generate(f(ast, "left"), state)
        state = generate(f(ast, "right"), state)
        cg_add_operation(STRCMP, state)
        return state

    if t == "time":
        cg_add_operation(TIME, state)
        return state

    if t == "delay":
        state = generate(f(ast, "value"), state)
        cg_add_operation(DELAY, state)
        return state

    if t == "rtc_read":
        cg_add_operation(RTC_READ, state)
        return state

    if t == "rtc_write":
        state = generate(f(ast, "value"), state)
        cg_add_operation(RTC_WRITE, state)
        return state

    if t == "fopen":
        state = generate(f(ast, "path"), state)
        cg_add_operation(FOPEN, state)
        return state

    if t == "fread":
        state = generate(f(ast, "fd"), state)
        cg_add_operation(FREAD, state)
        return state

    if t == "fwrite":
        state = generate(f(ast, "fd"), state)
        state = generate(f(ast, "string"), state)
        cg_add_operation(FWRITE, state)
        return state

    if t == "fclose":
        state = generate(f(ast, "fd"), state)
        cg_add_operation(FCLOSE, state)
        return state

    if t == "rand":
        cg_add_operation(RAND, state)
        return state

    if t == "srand":
        state = generate(f(ast, "seed"), state)
        cg_add_operation(SRAND, state)
        return state

    if t == "extern":
        extern_id = len(state["externs"])
        state["externs"][f(ast, "func_name")] = {
            "id": extern_id, "library": f(ast, "library"), "ret_type": "int"
        }
        return state

    if t == "alloc":
        # VM pops: segment (top), then size
        # So push size first, then segment on top
        state = generate(f(ast, "size"), state)
        cg_add_push("0", state)  # default segment = Main (0)
        cg_add_operation(ALLOC, state)
        return state

    if t == "alloc_seg":
        # alloc_seg(size, segment) — user specifies which segment
        state = generate(f(ast, "size"), state)
        state = generate(f(ast, "segment"), state)
        cg_add_operation(ALLOC, state)
        return state

    if t == "free":
        state = generate(f(ast, "handle"), state)
        cg_add_operation(FREE, state)
        return state

    if t == "load_h":
        state = generate(f(ast, "handle"), state)
        state = generate(f(ast, "index"), state)
        cg_add_operation(LOAD_H, state)
        return state

    if t == "store_h":
        state = generate(f(ast, "handle"), state)
        state = generate(f(ast, "index"), state)
        state = generate(f(ast, "value"), state)
        cg_add_operation(STORE_H, state)
        return state

    if t == "heap_len":
        state = generate(f(ast, "handle"), state)
        cg_add_operation(HEAP_LEN, state)
        return state

    if t == "region_enter":
        state = generate(f(ast, "segment"), state)
        cg_add_operation(REGION_ENTER, state)
        return state

    if t == "region_exit":
        state = generate(f(ast, "segment"), state)
        cg_add_operation(REGION_EXIT, state)
        return state

    if t == "seg_used":
        state = generate(f(ast, "segment"), state)
        cg_add_operation(SEG_USED, state)
        return state

    if t == "func_def":
        rt = f(ast, "ret_type")
        name = f(ast, "name")
        params = f(ast, "params")
        body = f(ast, "body")
        jmp_idx = len(state["bytecode"])
        state["bytecode"].append("JMP_PLACEHOLDER")
        func_start = len(state["bytecode"])
        state["functions"][name] = {
            "address": func_start, "ret_type": rt, "argc": len(params)
        }
        state["current_scope_locals"] = {}
        state["local_next_index"] = 0
        for pt, pn in params:
            state["current_scope_locals"][pn] = {
                "index": state["local_next_index"],
                "type": pt,
                "is_used": True,
            }
            state["local_next_index"] += 1
        for s in body:
            state = generate(s, state)
        if not state["bytecode"][-1].startswith(str(RET)):
            cg_add_push(0, state)
            cg_add_operation(RET, state)
        state["current_scope_locals"] = None
        state["bytecode"][jmp_idx] = f"{JMP} {len(state['bytecode'])}"
        return state

    if t == "func_call":
        name = f(ast, "name")
        args = f(ast, "args")
        if name in state["externs"]:
            for arg in args:
                state = generate(arg, state)
            extern_id = state["externs"][name]["id"]
            cg_add_operation(f"{CALL_EXTERN} {extern_id} {len(args)}", state)
        else:
            func = state["functions"][name]
            for arg in args:
                state = generate(arg, state)
            cg_add_operation(f"{CALL} {func['address']} {func['argc']}", state)
        return state

    if t == "return":
        state = generate(f(ast, "value"), state)
        cg_add_operation(RET, state)
        return state

    return state


# ===========================================================================
# Top-Level Compile
# ===========================================================================

def compile(source, package_name):
    src = "\n".join(source) if isinstance(source, list) else source
    tokens = lex(src)
    ast, _ = parse(tokens)
    env = make_env()
    check(ast, env)
    state = make_state(package_name)
    state = generate(ast, state)
    if not state["bytecode"] or not state["bytecode"][-1].startswith(str(HALT)):
        cg_add_operation(HALT, state)
    verify_usage(state)
    return state


def make_env():
    return {
        "variables": {},
        "functions": {},
        "externs": {},
        "current_locals": None,
    }


def format_bytecode(state):
    consts = [
        f"CONST {i} {v}" for i, v in enumerate(state["constant_pool"])
    ]
    if consts:
        consts = (
            ["# --- CONSTANT POOL ---"]
            + consts
            + ["# --- END CONSTANTS ---", ""]
        )
    strs = [
        f"STR {i} {s}" for i, s in enumerate(state["string_pool"])
    ]
    if strs:
        strs = (
            ["# --- STRING POOL ---"]
            + strs
            + ["# --- END STRINGS ---", ""]
        )
    arrs = [
        f"ARR {i} {','.join(map(str, v))}"
        for i, v in enumerate(state["array_pool"])
    ]
    if arrs:
        arrs = (
            ["# --- ARRAY POOL ---"]
            + arrs
            + ["# --- END ARRAYS ---", ""]
        )
    version_header = [
        f"VERSION 1",
        f"CONST_COUNT {len(state['constant_pool'])}",
        f"STR_COUNT {len(state['string_pool'])}",
        f"ARR_COUNT {len(state['array_pool'])}",
        "",
    ]
    package_header = [
        f"# Package: {state['package_name']}",
        "# Generated by ELIN Compiler",
        "#",
    ]
    return "\n".join(version_header + package_header + consts + strs + arrs + state["bytecode"])


def verify_usage(state):
    unused = [
        n for n, i in state["variables"].items() if not i["is_used"]
    ]
    if unused:
        print(f"Compilation Warning: Unused variables: {', '.join(unused)}")
        sys.exit(1)
