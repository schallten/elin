# Compiler Cleanup Plan

The compiler works, but it accumulated hacks as it grew. This plan cleans it up
without changing languages or derailing the self-hosting goal.

## Phase 1: Fix Expression Parsing

**Problem:** `parse_expression()` in `parser.py` slurps raw tokens until a stop
token, then rebuilds them into "prepared tokens," then string-mangles nodes
through `__NODE_i__` placeholders to reuse the old infix-to-postfix converter.
There are also two separate tree builders (`build_expr_tree` and
`build_expr_tree_from_nodes`) kept for "backwards compatibility."

**Goal:** Replace with a proper recursive-descent or Pratt parser that builds
the AST directly — no token-slurping, no node-to-string round-trip, no dead
code.

**Steps:**
1. Delete `expression_parser.py` (the infix-to-postfix converter).
2. Delete `build_expr_tree` and `build_expr_tree_from_nodes` from `parser.py`.
3. Implement operator precedence directly in `parse_expression` using a
   Pratt parser or simple precedence climbing.
4. Handle array access (`name[idx]`) as part of the primary expression parser
   instead of as a special case after token-slurping.

## Phase 2: Clean Up Code Generation

**Problem:** `Compiler.generate()` in `compiler.py` mixes typechecking, code
generation, and workarounds in one giant method. Hacks like
`register_internal_variable` exist because `PRINT` reads from a global slot
(roadmap item 1 fixes this).

**Goal:** Separate concerns so each pass does one thing.

**Steps:**
1. Move type inference (`infer_type`) and type checking out of `generate()`
   into a dedicated typecheck pass over the AST.
2. Remove `register_internal_variable` — once roadmap item 1 lands, PRINT pops
   from eval_stack directly and the temp variable hack is unnecessary.
3. Pull the bytecode formatting (string sections, headers) out of `compile()`
   into a dedicated `format_bytecode()` function. `compile()` should return
   raw instructions, not a formatted string.

## Phase 3: Delete Dead Code

**Problem:** There are multiple vestigial code paths.

**Steps:**
1. Delete `expression_parser.py`.
2. Remove the `stop_tokens` parameter from `parse_expression` — the new parser
   should know where expressions end naturally.
3. Remove the `# --- STRING POOL ---` / `# --- ARRAY POOL ---` section
   formatting from `Compiler` and move it to the formatter pass.
4. Clean up unused imports across all files.

## Phase 4: Clean Up the Parser Entry Points

**Problem:** `parse_condition()` is a separate method that handles simple
`token OP token` patterns, while `parse_expression()` handles everything else.
These should be unified.

**Steps:**
1. Remove `parse_condition()` — comparisons are just binary operators with
   lower precedence than math operators. Handle them in `parse_expression`.
2. Remove the comparison hack in `parse_expression` (lines checking
   `CMP_OPERATORS` on prepared tokens) — no longer needed once expression
   parsing is unified.

## Phase 5: Verify

**Goal:** Make sure nothing broke.

1. Compile `test.elin` and compare the output bytecode before and after each
   phase. The output should be identical (or functionally equivalent).
2. Run the C++ VM on the output to verify correct execution.
