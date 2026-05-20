# Haskell Compiler Rewrite Plan

This plan guides you through rewriting the Python compiler into Haskell, focusing on minimizing lines of code (LOC) by using Haskell's powerful features like Algebraic Data Types (ADTs) and Parser Combinators.

## Phase 1: Project Setup
**Goal:** Initialize the Haskell environment.
1. Run `stack new elin-compiler simple` or use `cabal init`.
2. Add dependencies to your `package.yaml` or `.cabal` file:
   - `megaparsec`: For parsing the source code without a separate lexer step.
   - `mtl`: For the `State` monad to track compiler variables and generated instructions.
   - `text`: For efficient string handling.

## Phase 2: Define the Unified AST (`AST.hs`)
**Goal:** Replace Python's class hierarchy and visitor pattern with simple Haskell ADTs.
1. Create `AST.hs`.
2. Define a single `Expr` type that combines operations (`ops.py`) and expressions.
   ```haskell
   data Expr
     = Number Int
     | String Literal
     | Add Expr Expr
     | Var String
     -- Add other nodes here
     deriving (Show, Eq)
   ```
3. Define a `Stmt` type for statements (like variable declarations, loops, and function definitions).
*Why this saves LOC:* Haskell's pattern matching will replace the verbose Python Visitor pattern.

## Phase 3: The Scannerless Parser (`Parser.hs`)
**Goal:** Skip the Lexer entirely and parse raw text directly into the AST.
1. Create `Parser.hs` and import `Text.Megaparsec` and `Text.Megaparsec.Char`.
2. Define basic parsers for whitespace and tokens (e.g., parsing a number or an identifier).
3. Use `Control.Monad.Combinators.Expr.makeExprParser`. This automatically handles operator precedence (replaces `expression_parser.py` and the manual Pratt parsing).
4. Write parsers for your `Stmt` types.

## Phase 4: The Compiler Core (`Compiler.hs`)
**Goal:** Traverse the AST and generate target code (or evaluate directly).
1. Create `Compiler.hs` and import `Control.Monad.State`.
2. Define your compiler state (e.g., current scope, generated instructions list).
   ```haskell
   type CompilerState = [Instruction]
   ```
3. Write a `compileExpr :: Expr -> State CompilerState ()` function.
4. Use pattern matching to handle each AST node. Instead of overriding `visit_Add`, you just do:
   ```haskell
   compileExpr (Add left right) = do
       compileExpr left
       compileExpr right
       emit OpAdd
   ```
*Why this saves LOC:* No class boilerplate. Code generation maps 1:1 with the AST structure.

## Phase 5: Main Entry Point (`Main.hs`)
**Goal:** Tie the pipeline together.
1. In `Main.hs`, read a file (e.g., `test.elin`).
2. Pass the file content to your Megaparsec parser.
3. If parsing succeeds, pass the AST to `execState` with your compiler function.
4. Print or write the output.

## Phase 6: Testing
**Goal:** Verify the Haskell rewrite.
1. Run `stack run test.elin`.
2. Ensure the output matches the behavior of your old Python compiler.
