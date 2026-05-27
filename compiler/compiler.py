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
)
from ast_nodes import *
from lexer import lex
from parser import parse


# --- Type-checking environment ---

def make_env():
    return {
        "variables": {},
        "functions": {},
        "current_locals": None,
    }


def tc_infer_type(node, env):
    match node:
        case NumberNode():
            return "int"
        case StringNode():
            return "str"
        case VariableNode(name=n):
            loc = env["current_locals"]
            if loc and n in loc:
                return loc[n]
            if n in env["variables"]:
                return env["variables"][n]
            raise Exception(f"Type Error: Variable '{n}' undefined.")
        case UnaryOpNode(operand=oper):
            t = tc_infer_type(oper, env)
            if t != "int":
                raise Exception(f"Type Error: Unary needs int, got {t}")
            return "int"
        case BinaryOpNode(left=l, right=r):
            lt = tc_infer_type(l, env)
            rt = tc_infer_type(r, env)
            if lt != "int" or rt != "int":
                raise Exception(f"Type Error: Math needs int, got {lt}, {rt}")
            return "int"
        case ConditionNode():
            return "int"
        case ArrayNode(elements=elts):
            if not elts:
                return "arr int"
            return f"arr {tc_infer_type(elts[0], env)}"
        case ArrayAccessNode(name=n):
            t = tc_get_var_type(n, env)
            return t.split(" ", 1)[1] if " " in t else "int"
        case ArrayLenNode():
            return "int"
        case AbsNode():
            return "int"
        case InputNode():
            return "int"
        case FunctionCallNode(name=n):
            funcs = env["functions"]
            if n not in funcs:
                raise Exception(f"Type Error: Function '{n}' undefined")
            return funcs[n]["ret_type"]
        case _:
            return "unknown"


def tc_get_var_type(name, env):
    loc = env["current_locals"]
    if loc and name in loc:
        return loc[name]
    if name in env["variables"]:
        return env["variables"][name]
    raise Exception(f"Type Error: Variable '{name}' undefined")


def check(ast, env):
    match ast:
        case ProgramNode(statements=stmts):
            for s in stmts:
                env = check(s, env)
            return env
        case AssignNode(type_name=tn, name=n, value=v):
            vt = tc_infer_type(v, env)
            if tn != vt:
                raise Exception(f"Type Error: {vt} -> {tn}")
            if env["current_locals"] is not None:
                env["current_locals"][n] = tn
            else:
                env["variables"][n] = tn
            return check(v, env)
        case ReassignNode(name=n, value=v):
            vt = tc_infer_type(v, env)
            et = tc_get_var_type(n, env)
            if vt != et:
                raise Exception(f"Type Error: {vt} -> {et}")
            return check(v, env)
        case PrintNode(value_node=vn):
            return check(vn, env)
        case IfNode(condition=cond, body=body, else_body=else_body):
            check(cond, env)
            for s in body:
                env = check(s, env)
            for s in else_body:
                env = check(s, env)
            return env
        case WhileNode(condition=cond, body=body):
            check(cond, env)
            for s in body:
                env = check(s, env)
            return env
        case FunctionDefNode(ret_type=rt, name=n, params=params, body=body):
            param_types = [pt for pt, pn in params]
            env["functions"][n] = {"ret_type": rt, "params": param_types}
            old = env["current_locals"]
            env["current_locals"] = {pn: pt for pt, pn in params}
            for s in body:
                env = check(s, env)
            env["current_locals"] = old
            return env
        case FunctionCallNode(name=n, args=args):
            funcs = env["functions"]
            if n not in funcs:
                raise Exception(f"Type Error: Function '{n}' undefined")
            info = funcs[n]
            if len(args) != len(info["params"]):
                raise Exception(
                    f"Type Error: {n} expects {len(info['params'])} args, got {len(args)}"
                )
            for i, arg in enumerate(args):
                at = tc_infer_type(arg, env)
                if at != info["params"][i]:
                    raise Exception(f"Type Error: Arg {i} {at} -> {info['params'][i]}")
            return env
        case UnaryOpNode(operand=oper):
            return check(oper, env)
        case BinaryOpNode(left=l, right=r):
            check(l, env)
            return check(r, env)
        case ConditionNode(left=l, right=r):
            check(l, env)
            return check(r, env)
        case ArrayAssignNode(index=idx, value=v):
            check(idx, env)
            return check(v, env)
        case AbsNode(value=v):
            return check(v, env)
        case InputNode():
            return env
        case ReturnNode(value=v):
            return check(v, env)
        case _:
            return env


# --- Code-generation state ---

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
    match node:
        case StringNode():
            return "str"
        case VariableNode(name=n):
            if state["current_scope_locals"] and n in state["current_scope_locals"]:
                return state["current_scope_locals"][n]["type"]
            return state["variables"][n]["type"]
        case FunctionCallNode(name=n):
            return state["functions"][n]["ret_type"]
        case _:
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
    match ast:
        case ProgramNode(statements=stmts):
            for s in stmts:
                state = generate(s, state)
            return state

        case AssignNode(type_name=tn, name=n, value=v):
            idx, local = cg_register_variable(n, tn, state)
            state = generate(v, state)
            cg_add_store(idx, local, state)
            return state

        case ArrayAssignNode(name=n, index=idx_node, value=v):
            idx, local = cg_lookup_variable_index(n, state)
            cg_add_load(idx, local, state)
            state = generate(idx_node, state)
            state = generate(v, state)
            cg_add_operation(ARR_SET, state)
            return state

        case ReassignNode(name=n, value=v):
            # Optimize x = x + 1 -> INC and x = x - 1 -> DEC
            if isinstance(v, BinaryOpNode):
                vn = v
                if (isinstance(vn.left, VariableNode) and vn.left.name == n
                        and isinstance(vn.right, NumberNode) and vn.right.value == "1"):
                    idx, local = cg_lookup_variable_index(n, state)
                    if vn.op == "+":
                        cg_add_operation(f"{INC} {idx}", state)
                    elif vn.op == "-":
                        cg_add_operation(f"{DEC} {idx}", state)
                    return state
            idx, local = cg_lookup_variable_index(n, state)
            state = generate(v, state)
            cg_add_store(idx, local, state)
            return state

        case PrintNode(value_node=vn):
            state = generate(vn, state)
            cg_add_operation(
                PRINT_STR if cg_infer_type(vn, state) == "str" else PRINT,
                state,
            )
            return state

        case IfNode(condition=cond, body=body, else_body=else_body):
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

        case WhileNode(condition=cond, body=body):
            start = len(state["bytecode"])
            state = generate(cond, state)
            jz_idx = len(state["bytecode"])
            state["bytecode"].append("JZ_PLACEHOLDER")
            for s in body:
                state = generate(s, state)
            cg_add_operation(f"{JMP} {start}", state)
            state["bytecode"][jz_idx] = f"{JZ} {len(state['bytecode'])}"
            return state

        case HaltNode():
            cg_add_operation(HALT, state)
            return state

        case UnaryOpNode(op=op, operand=oper):
            if isinstance(oper, NumberNode):
                a = int(oper.value)
                if op == "-":
                    val = -a
                elif op == "!":
                    val = 1 if a == 0 else 0
                cg_add_push(str(val), state)
                return state
            state = generate(oper, state)
            cg_add_operation(NEG if op == "-" else NOT, state)
            return state

        case ConditionNode(op=op, left=l, right=r):
            if isinstance(l, NumberNode) and isinstance(r, NumberNode):
                a, b = int(l.value), int(r.value)
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
            cg_add_operation(CMP_OP_MAP[op], state)
            return state

        case BinaryOpNode(op=op, left=l, right=r):
            if isinstance(l, NumberNode) and isinstance(r, NumberNode):
                a, b = int(l.value), int(r.value)
                if op == "+": val = a + b
                elif op == "-": val = a - b
                elif op == "*": val = a * b
                elif op == "/": val = a // b if b != 0 else 0
                elif op == "%": val = a % b if b != 0 else 0
                cg_add_push(str(val), state)
                return state
            state = generate(l, state)
            state = generate(r, state)
            cg_add_operation(OP_MAP[op], state)
            return state

        case NumberNode(value=v):
            cg_add_push(v, state)
            return state

        case StringNode(value=s):
            cg_add_push_str(s, state)
            return state

        case VariableNode(name=n):
            idx, local = cg_lookup_variable_index(n, state)
            cg_add_load(idx, local, state)
            return state

        case ArrayNode(elements=elts):
            all_lit = all(isinstance(e, (NumberNode, StringNode)) for e in elts)
            if all_lit:
                vals = []
                for e in elts:
                    if isinstance(e, StringNode):
                        pool = state["string_pool"]
                        if e.value not in pool:
                            pool.append(e.value)
                        vals.append(pool.index(e.value))
                    else:
                        vals.append(e.value)
                cg_add_push_arr(vals, state)
            else:
                for e in elts:
                    state = generate(e, state)
                cg_add_operation(f"{MAKE_ARR} {len(elts)}", state)
            return state

        case ArrayAccessNode(name=n, index=idx_node):
            idx, local = cg_lookup_variable_index(n, state)
            cg_add_load(idx, local, state)
            state = generate(idx_node, state)
            cg_add_operation(ARR_GET, state)
            return state

        case ArrayLenNode(name=n):
            idx, local = cg_lookup_variable_index(n, state)
            cg_add_load(idx, local, state)
            cg_add_operation(ARR_LEN, state)
            return state

        case AbsNode(value=v):
            state = generate(v, state)
            cg_add_operation(ABS, state)
            return state

        case InputNode():
            cg_add_operation(INPUT, state)
            return state

        case FunctionDefNode(ret_type=rt, name=n, params=params, body=body):
            jmp_idx = len(state["bytecode"])
            state["bytecode"].append("JMP_PLACEHOLDER")
            func_start = len(state["bytecode"])
            state["functions"][n] = {
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

        case FunctionCallNode(name=n, args=args):
            func = state["functions"][n]
            for arg in args:
                state = generate(arg, state)
            cg_add_operation(f"{CALL} {func['address']} {func['argc']}", state)
            return state

        case ReturnNode(value=v):
            state = generate(v, state)
            cg_add_operation(RET, state)
            return state

        case _:
            return state


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
