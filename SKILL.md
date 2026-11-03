---
name: pylgen
description: Use when writing or debugging code that uses PyLGEN (`pylgen-core` on PyPI, `import pylgen`), a Python-native compiler/interpreter framework — regex→DFA lexer, attributed grammars with `+=`, LALR(1)/SLR/LR(1) parser generation, AST + visitor framework, optional HTML visualization, Cython acceleration. Triggers on "pylgen", "pylgen-core", "AttributedGrammar", "ParserBuilder", "ASTListView", "IdentedLexer", or building a lexer/parser/DSL/interpreter in Python with this library.
---

# PyLGEN (`pylgen-core`) — working reference

**Version covered:** 0.7.3 (2026-10-20). Python ≥ 3.12. BSD-3. Author: YonyUk.
**Install:** `pip install pylgen-core` · extras `[visual]` (networkx, pyvis, matplotlib) `[cython]` `[test]` `[all]`.
**Links:** docs https://pylgen.readthedocs.io/en/latest · repo https://github.com/yonyuk/pylgen · PyPI https://pypi.org/project/pylgen-core/

This file is the cheat sheet. Full material lives beside it:

| Need | Read |
|---|---|
| Exact class/method signatures | `reference/03-api-reference-python.md` |
| How each module is meant to be used, with examples | `reference/02-user-guide.md` |
| Minimal end-to-end interpreter | `reference/01-getting-started.md` (Quick Start section) |
| Changelog / breaking changes | `reference/00-readme-and-changelog.md` |
| Visitors, context, runtime errors in practice | `examples/arithmetic_interpreter/` |
| Indentation-sensitive language (`IdentedLexer`) | `examples/idented_dsl/`, `reference/tutorials/config-dsl-indented.md` |
| Large real language (scopes, functions, error ASTs) | `examples/mini-python/`, `reference/tutorials/mini-python.md` |
| Cython-compiled language, `cdef` reducers | `reference/tutorials/veclang.md`, `reference/04-api-reference-cython.md` |
| Building a lexer/LR parser from the primitives | `reference/tutorials/foundations.md` |
| Theory (automata, FIRST/FOLLOW, LR items) | `reference/05-formal-foundations.md` |

Grep these files rather than reading them whole; the tutorials are 25–170 KB each.

## Mental model

```
text → Lexer → Iterable[Token] → Parser.parse() → AST (built by your reducers) → ASTWalker/visitors → result
```

- **You own every stage.** No grammar files, no code generation. Grammar is Python objects; reducers are Python functions; AST node classes are yours.
- **Nothing is magic:** there is no default reducer, no default AST node type, no default visitor traversal. The framework supplies the LALR tables and the plumbing; you supply the semantics.
- Errors accumulate; they do not raise. Check `lexer.errors`, `parser.errors` / `parser.syntax_errors`, `context.errors`.

## Module map (`pylgen.<module>`)

| Module | Exports you'll use |
|---|---|
| `common.enums` | `TokenType` (StrEnum base; subclasses auto-get `INVALID_TOKEN`), `ErrorType` |
| `common.types` | `Symbol`, `AST`, `Token`, `ASTListView`, `ErrorAST`, `Error`, `LexicalError`, `SyntaxError`, `SemanticError`, `RuntimeError` |
| `lexer` | `Lexer`, `IdentedLexer`, `BaseLexer` |
| `grammar` | `Grammar`, `AttributedGrammar`; `grammar.grammar.Production`, `ProductionsSet`, `AttributedProductionsSet` |
| `parser` | `ParserBuilder`, `ParserType`, `Parser`, `BottomUpParser`, `ParseTreeNode`; conflict exceptions in `parser.parser_builder` |
| `analysis` | `Context`, `ASTVisitor`, `ASTWalker`, `TraversalStrategy`, `ASTChildrenSelector`, `LexicalRule` |
| `regex` | `RegexEngine` (regex → NFA/DFA; used by the lexer) |
| `automaton` | `DFA`, `NFA`, `State`, `Automaton`, `create_dfa`, `create_nfa`, `get_word(s)_automaton[_with_value]` |
| `visual` | `draw_ast`, `draw_parse_tree`, `draw_automaton`, `draw_lexer`, `lr_inspect_grammar`, `show_propagation_edges_table`, `set_cache_file` (needs `[visual]`) |

Note: the package's own `SyntaxError` / `RuntimeError` **shadow Python builtins** if you `from pylgen.common.types import *`. Import explicitly or alias.

## Canonical pipeline (copy this shape)

```python
from pylgen.common.enums import TokenType
from pylgen.common.types import Symbol, AST, Token, ASTListView
from pylgen.lexer import Lexer
from pylgen.grammar import AttributedGrammar
from pylgen.parser import ParserBuilder, ParserType

# 1. Token types — subclass TokenType; INVALID_TOKEN is injected automatically
class Tok(TokenType):
    NUMBER = "NUMBER"; PLUS = "PLUS"; MINUS = "MINUS"; STAR = "STAR"; SLASH = "SLASH"
    LPAREN = "LPAREN"; RPAREN = "RPAREN"; EOF = "EOF"

# 2. Symbols — Symbol(name, is_terminal=False, is_epsilon=False)
E, T, F = Symbol("E"), Symbol("T"), Symbol("F")                   # non-terminals
number, plus, minus = Symbol("number", True), Symbol("+", True), Symbol("-", True)
star, slash, lp, rp = Symbol("*", True), Symbol("/", True), Symbol("(", True), Symbol(")", True)

# 3. Lexer — mapping fn MUST be annotated (TokSubclass, str) -> Symbol; validated via inspect
def to_symbol(t: Tok, text: str) -> Symbol:
    return {Tok.NUMBER: number, Tok.PLUS: plus, Tok.MINUS: minus, Tok.STAR: star,
            Tok.SLASH: slash, Tok.LPAREN: lp, Tok.RPAREN: rp}.get(t, Symbol(text, True))

lexer = Lexer(to_symbol, ignore_pattern=r"\s+")
lexer.set_eof_token("$", Tok.EOF)            # EOF symbol text must equal grammar end_symbol
lexer[0, Tok.NUMBER] = r"\d+(\.\d+)?"        # lexer[priority, type] = regex ; lower priority wins ties
lexer[1, Tok.LPAREN] = r"\("
lexer[2, Tok.RPAREN] = r"\)"
lexer[3, Tok.STAR]   = r"\*"
lexer[4, Tok.SLASH]  = r"/"
lexer[5, Tok.PLUS]   = r"\+"
lexer[6, Tok.MINUS]  = r"\-"

# 4. AST nodes — subclass AST, call super().__init__(symbol, sl, sc, el, ec), implement children()
class NumberAST(AST):
    def __init__(self, token: Token):
        (l, c) = token.start_position
        super().__init__(token.symbol, l, c, l, c + len(token.text))
        self.value = token.text
    def children(self): return []

class BinaryOpAST(AST):
    def __init__(self, left: AST, right: AST, op: Symbol):
        (sl, sc), (el, ec) = left.start_position, right.end_position
        super().__init__(op, sl, sc, el, ec)
        self.left, self.right = left, right
    def children(self): return [self.left, self.right]

# 5. Reducers — MUST be annotated (ASTListView) -> AST; validated at `+=` time
def num(asts: ASTListView) -> AST: return NumberAST(asts[0])
def binop(asts: ASTListView) -> AST: return BinaryOpAST(asts[0], asts[2], asts[1].symbol)
def single(asts: ASTListView) -> AST: return asts[0]
def paren(asts: ASTListView) -> AST: return asts[1]

# 6. Attributed grammar — G[head] += (rhs_tuple), reducer
G = AttributedGrammar(E, end_symbol="$")
G[E] += (E, plus, T), binop
G[E] += (E, minus, T), binop
G[E] += (T,), single                          # note trailing comma for 1-symbol RHS
G[T] += (T, star, F), binop
G[T] += (T, slash, F), binop
G[T] += (F,), single
G[F] += (lp, E, rp), paren
G[F] += (number,), num

# 7. Parser
parser = ParserBuilder.build_parser_from_attributed(G, ParserType.LALR1)

# 8. Run
lexer.load_text("2 * (4 / 2 - 3) + 1")
ast = parser.parse(lexer.tokens)              # returns root AST, or None on failure
if lexer.errors or parser.syntax_errors:
    for e in [*lexer.errors, *parser.errors]: print(e)
```

## Key API facts & gotchas

**Lexer**
- `Lexer(get_symbol_function, ignore_pattern: str)`; `IdentedLexer` same ctor plus `set_ident(Tok.X)`, `set_indent_symbol(sym)`, `set_dedent_symbol(sym)`, `set_text_sanitize_function(fn)`.
- Token patterns: `lexer[priority, Tok.X] = regex` or `lexer.add_token_regex(priority, Tok.X, regex)`. Longest match wins; on equal length, lower priority number wins → put keywords before identifiers.
- The regex engine is PyLGEN's own (`pylgen.regex`), not `re`. Supported: literals, `.`, classes `[abc] [^abc] [a-z]`, `\d \D \s \S \w \W`, quantifiers `* + ? {min,max}`, alternation `|`, groups `( )`, escapes `\( \) \[ \] \{ \} \- \* \+ \? \^ \| \. \,`. Alphabet = `string.printable` + Latin accented vowels/ñ/ü + `¿ ¡ « »` (since 0.7.2). **Not** supported: lookaround, backreferences, non-greedy quantifiers, named groups, `\b`. Full list: `reference/02-user-guide.md` §"Supported Syntax".
- `lexer.tokens` is a generator; it initializes the DFA on first use and appends the EOF token if `set_eof_token` was called. `load_text()` resets position counters.
- `lexer.errors` → `Set[LexicalError]`; `clear_errors()`. Unmatched text becomes `INVALID_TOKEN` + a `LexicalError`; tokenization continues.
- Extra validation beyond regex: subclass `analysis.lexical.LexicalRule(msg)`, implement `_check(self, text) -> bool`, register with `lexer.add_rule(Tok.X, rule)`.
- Mapping function annotations are enforced with `inspect`: first param annotated with your `TokenType` subclass, second `str`, return `Symbol`. Missing annotations → `ValueError`/init failure.

**Grammar**
- `Symbol` equality/hash = (name, is_terminal, is_epsilon). Reuse the same `Symbol` objects between lexer mapping and grammar.
- Epsilon: `eps = Symbol("ε", is_terminal=True, is_epsilon=True)`; only one epsilon symbol per grammar (`ValueError` otherwise). Use `G[A] += (eps,), reducer`.
- `Grammar.first(seq)`, `Grammar.follow(sym)` compute lazily; `Grammar.AugmentGrammar(g)` / `Reverse(g)` are static. `to_dict()` for debugging.
- Every production in an `AttributedGrammar` needs a reducer — there is no default. A reduction without one fails.
- `ASTListView` is read-only: `len()`, `asts[i]`. Items are whatever earlier reducers returned, or `Token` for terminals (`Token` is itself an `AST` subclass with `.text`, `.type`, `.symbol`).

**Parser**
- `ParserType.LALR1` (recommended), `SLR`, `LR1`; `LL1` exists in the enum but is **not supported**.
- Conflicts raise at build time: `LALRShiftReduceConflictException`, `LALRReduceReduceConflictException` (and SLR/LR1 variants), carrying `.state`, `.symbol`, `.production` / `.old`, `.new_`. To inspect visually: `pylgen.visual.lr_inspect_grammar(G, ParserType.LALR1, ...)`.
- `parser.parse(tokens)` never raises on syntax errors; it does panic-mode recovery and accumulates `parser.errors`. Check `parser.syntax_errors` (bool) before semantic analysis — `parser.errors` may also contain semantic errors attached via `ErrorAST` nodes.
- Parse tree (distinct from AST): `parser.set_draw_parse_tree_flag(True)` before parsing, then `parser.parse_tree` (`ParseTreeNode` with `.symbol`, `.start_position`, `.end_position`, `.children` — note `.children` property, renamed from `childrens` in 0.7.3).
- `Parser.reset()` is documented as not implemented in the base; rebuild or re-`parse` instead of relying on it.

**AST / positions / errors**
- `AST(symbol, start_line, start_column, end_line, end_column)`; properties `start_position`, `end_position` (tuples), `is_error`, `symbol`; abstract `children()`. `str(ast)` = symbol name.
- `ErrorAST(symbol, ..., errors: Set[SemanticError])` — an AST node that carries semantic errors and sets `is_error=True`; use it from reducers to report semantic problems during parsing.
- Error classes: `LexicalError(msg, sl, sc, el, ec)`, `SyntaxError(...)`, `SemanticError(...)`; `RuntimeError(stack_trace: List[str], sl, sc, el, ec, msg)` exposes `.stack_trace` instead of a message-only ctor. All have `.type: ErrorType`, `.message`, `.start_position`, `.end_position`.

**Analysis (visitor framework)** — see `examples/arithmetic_interpreter/visitors.py`, `semantic.py`, `context.py`
- Subclass `Context`; the base raises `NotImplementedError` for `push_new_scope`, `pop_scope`, `add_runtime_error(ast, err)`, `clear_runtime_errors`, `get_runtime_errors` — override the ones you call. `add_semantic_error`, `clear_semantic_errors`, `clear_errors`, `reset`, `push_trace/pop_trace`, `.errors`, `.stack_trace` work out of the box.
- `ASTVisitor(context_type)`: implement `visit(self, ast: YourNode, context: YourContext)`. `ASTChildrenSelector(context_type)`: implement `select_children(self, ast, context) -> List[AST]` (usually `return ast.children()`). `TraversalStrategy(context_type)`: implement `init(root)`, `has_next()`, `current(context) -> AST`, `reset()`; use `self._get_selector(ast)` inside. **There is no built-in pre/post-order strategy** — write one (the arithmetic example has a ~25-line `PostOrderStrategy`).
- Wiring: `strategy.set_default_selector(sel)`; `walker = ASTWalker(context, strategy)`; `walker.add_visitor(NodeType, visitor)`; `walker.set_default_visitor(v)`; `walker.walk(ast)`. Dispatch is by exact `type(ast)` with fallback to the default visitor.
- Context-type annotations on `visit`/`select_children` are checked with `inspect` against `context_type` → `TypeError` if they don't match. Annotate them.
- Common pattern: evaluators store per-node values in the context (`context.add_ast_value(ast, v)` / `get_ast_value`) during a post-order walk, so parents read children's values.

**Visual** (`pip install pylgen-core[visual]`)
- `draw_ast(ast, show=True, filename="ast")`, `draw_parse_tree(tree, ...)`, `draw_automaton(dfa, ...)`, `draw_lexer(lexer, ...)`, `lr_inspect_grammar(G, ParserType.LALR1, ...) -> bool`, `show_propagation_edges_table(G, ...)`. All take `**kwargs` (`show`, `filename`, `cache`). Output is pyvis HTML referencing CDN assets; for offline/self-contained HTML call `set_cache_file("cache.pkl")` once then pass `cache=True` (passing `cache=True` without `set_cache_file` → `ValueError`).

**Cython**
- Python API works unchanged; Cython path uses `cimport` and `cdef`/`cpdef` reducers (`cdef AST reducer(ASTListView asts)` using `asts._get(i)`), `G._add_attributed_production(head, [rhs], reducer)`, `lexer._enum_type = Tok`, `_build_lalr_parser_from_attribute(G)`. Requires a C compiler. Details: `reference/04-api-reference-cython.md`, `reference/tutorials/veclang.md`.

## Breaking changes to watch for (if code targets an older version)

- **0.7.3** `ParseTreeNode.childrens` → `.children`.
- **0.7.2** Lexer alphabet widened beyond `string.printable`; `[^...]`, `.`, `\D \S \W` now complement against the extended alphabet.
- **0.7.0** `AST.__init__` takes `(symbol, start_line, start_column, end_line, end_column)` — was `(symbol, line, column)`; `.line/.column` replaced by `.start_position/.end_position`. `ErrorType` moved to `pylgen.common.enums`; `Error`, `LexicalError`, `SyntaxError`, `SemanticError`, `RuntimeError` moved from `pylgen.analysis.error` to `pylgen.common.types`.

## Debugging checklist

1. Lexer silently produces `INVALID_TOKEN`? → check `lexer.errors`; a regex feature may be unsupported by `pylgen.regex`; verify priorities.
2. `ValueError` on `Lexer(...)` or `G[...] +=` → missing/incorrect type annotations on the mapping function or reducer.
3. Conflict exception at `build_parser_from_attributed` → read `.state`/`.symbol`/`.production`; try `lr_inspect_grammar`; refactor grammar (precedence by layering non-terminals like E/T/F).
4. `parse()` returns `None` → `parser.errors`; make sure `set_eof_token` symbol text equals `AttributedGrammar(..., end_symbol=...)`.
5. Reducer `KeyError`/failure → a production has no reducer, or wrong index into `ASTListView`.
6. `TypeError` from `add_visitor`/`add_selector` → `context` param annotation doesn't match the `context_type` passed to the constructor.
7. `NotImplementedError` from `Context` → override the scope/runtime-error methods you use.
