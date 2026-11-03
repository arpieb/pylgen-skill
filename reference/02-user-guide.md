# PyLGEN — User Guide



<!-- source: docs/user-guide/user-guide-intro.md -->

# User Guide

This section explains how to use PyLGEN's modules. For the full signature and attribute listing of each class, see the [API Reference](../api-reference/table_of_contents.md).

## How to read this section

- If this is your first time here, start with the [First Steps](../getting-started/installation.md). This guide assumes you have already built something.
- If you are coming from the [Quick Start](../getting-started/quick-start.md) guide, read `Lexer` → `Grammar` → `Parser` → `Analysis`. The `Common` module serves as a cross-reference for the types that appear throughout all those modules; consult it whenever you need to check an exact signature. `Regex` and `Automaton` are independent modules, useful if you want to build automata or work directly with regular expressions. `Visual` is intended for debugging and presentation purposes.

## Module Map

| Module | Responsibility | Page |
| :--- | :--- | :--- |
| `lexer` | Tokenization using regex and lexical rules. | [Lexer](user-guide-lexer.md) |
| `grammar` | Productions, attributed grammars, reducers. | [Grammars](user-guide-grammar.md) |
| `parser` | Construction and execution of the LALR(1) parser. | [Parser](user-guide-parser.md) |
| `analysis` | Visitors, walkers, context, semantic analysis. | [Semantic Analysis](user-guide-analysis.md) |
| `common` | Base types: `Symbol`, `AST`, `Token`, `Error`, `ASTListView`. | [common](user-guide-common.md) |
| `regex` | Regular expression engine. | ​​[Regular Expressions](user-guide-regex.md) |
| `automaton` | DFA, NFA, and language operations. | [Automata](user-guide-automaton.md) |
| `visual` | Interactive HTML visualization. | [Visualization](user-guide-visual.md) |



<!-- source: docs/user-guide/user-guide-common.md -->

# The **`common`** Module

The `common` module is not used in isolation. It appears at every stage of the pipeline: tokens are of type `Token`, grammar symbols are `Symbol`, tree nodes are subclasses of `AST`, and errors are subclasses of `Error`.

## `Symbol`

A `Symbol` represents a grammar symbol: either a terminal (token) or a non-terminal (a category that expands).

**Python:**

```python
from pylgen.common.types import Symbol

# Non-terminal: 'E' (expression)
E = Symbol('E')

# Terminal: the '+' sign
plus = Symbol('+', is_terminal=True)

# Epsilon (always a terminal)
eps = Symbol('ε', is_terminal=True, is_epsilon=True)
```

**Cython:**
```cython
from pylgen.common.types cimport Symbol

# Non-terminal: 'E' (expression)
cdef Symbol E = Symbol('E')

# Terminal: the '+' sign
cdef Symbol plus = Symbol('+', is_terminal=True)

# Epsilon (always a terminal)
cdef Symbol eps = Symbol('ε', is_terminal=True, is_epsilon=True)
```

> ### Attributes

| **`Attribute`** | **`Type`** | **Default** | **Description** |
| :---: | :---: | :---: | :---: |
| **`symbol`** | `str` | **required** | Symbol text |
| **`is_terminal`** | `bool` | `False` | `True` if it is a terminal |
| **`is_epsilon`** | `bool` | `False` | `True` if it is the ε symbol (implies terminal) |

> **IMPORTANT: `Symbol`'s Equality**
Two `Symbol`'s are equal if their three attributes match. This is important: `Symbol("+")` and `Symbol("+", is_terminal=True)` are not the same symbol.

## `AST`

`AST` is the abstract base class for all **Abstract Syntax Tree** nodes. Every node you build must inherit from it and, at a minimum, implement the `children()` method, which returns the list of its child nodes (sub‑ASTs). The base implementation of `children()` raises `NotImplementedError`, so you are required to override it in concrete subclasses.

**Python:**

```python
from pylgen.common.types import AST, Symbol

class BinaryOpAST(AST):
    def __init__(self, left: AST, right: AST, symbol: Symbol):
        (start_line,start_column),(end_line,end_column) = left.start_position,right.end_position
        super().__init__(symbol, start_line, start_column, end_line, end_column)
        self._left = left
        self._right = right

    def children(self) -> List[AST]:
        return [self._left, self._right]
```
**Cython:**
```cython
from pylgen.common.types cimport AST

cdef class BinaryOpAST(AST):
    cdef AST _left
    cdef AST _right
    cdef list[AST] _childs

    def __init__(self,AST left, AST right, Symbol symbol):
        super().__init__(symbol,left._start_line,left._start_column,right._end_line,right._end_column)
        self._left = left
        self._right = right
        self._childs = [left,right]

    cpdef list[AST] children(self):
        return self._childs
```

> **TIP: Best Practice**
Always declare attributes as `cdef` with concrete types whenever possible. This speeds up access and assignment in reducers and visitors.

> ### Attributes and Methods

| **Attribute/Method** | **Type/Return** | **Description** |
| :---: | :---: | :---: |
| **`symbol` (property)** | `Symbol` | The grammar symbol associated with this node. |
| **`start_position` (property)** | `Tuple[int, int]` | `(start_line, start_column)` where the node starts. |
| **`end_position` (property)** | `Tuple[int, int]` | `(end_line, end_column)` where the node ends. |
| **`is_error` (property)** | `bool` | Indicates whether this node represents a semantic error. Always `False` for `AST`; overridden in `ErrorAST` | 
| `children()` (method) | `List[AST]` | Returns a list of child AST nodes. Must be overridden. |

> **NOTE**
Both, `start_position` and `end_position` are 1-indexed, this means that index 1 points to 0 real index in a list.

> **WARNING: Validation**
The constructor of AST raises a `ValueError` if `start_line` or `start_column` are negative, if `end_line < start_line`, or if `end_line == start_line` and `end_column <= start_column`. The setters for `start_position` and `end_position` perform similar checks.

> **NOTE: String Representation**
Both `__str__` and `__repr__` return the string representation of the internal `Symbol` (i.e., the symbol’s name). This makes debugging and logging more convenient.

## Error Hierarchy

A robust error handling system is essential for any language implementation. PyLGEN provides a unified, hierarchical error model that spans all phases of the compilation pipeline, from lexing to runtime execution. Every error carries precise location information (start and end position) and a descriptive message, making it easy to report problems directly to the user.

The hierarchy is built around a common base class `Error`, with specialized subclasses for each stage of processing. All errors are collected in the `Context` (semantic and runtime) or in the lexer/parser themselves (lexical and syntax), allowing you to aggregate and report multiple issues in a single pass.

> ### `ErrorType` (Enumeration)

The `ErrorType` enum (`pylgen.common.enums`) categorises errors by their origin:

```python
from enum import StrEnum

class ErrorType(StrEnum):
    LEXICAL = 'LEXICAL'
    SYNTAX = 'SYNTAX'
    SEMANTIC = 'SEMANTIC'
    RUNTIME = 'RUNTIME'
```

These values are used internally to tag each error and to format user‑friendly messages.

> ### `Error` Base Class

`Error` is the abstract base class for all compile‑time errors (lexical, syntax, semantic) and also for runtime errors. It provides the common attributes and formatting logic.

| **Attribute/Property** | **Type** | **Description** |
| :---: | :---: | :---: |
| **`start_position` (property)** | `Tuple[int, int]` | `(start_line, start_column)` where the error starts. |
| **`end_position` (property)** | `Tuple[int, int]` | `(end_line, end_column)` where the error ends. |
| **`type`** | `ErrorType` | The category of the error. |
| **`message`** | `str` | A human‑readable error message, formatted as `"{type} ERROR at line {line}: {msg}"`. |

The constructor accepts the error type (either a member of `ErrorType` or a string that matches one of its values), the `start_line`/`start_column` number, the `end_line`/`end_column` number, and a custom message. If a string is given, it is internally converted to the corresponding `ErrorType` member; otherwise, a `TypeError` or `ValueError` is raised.

> ### Concrete Error Classes

| **Class** | **Description** |
| :---: | :---: |
| **`LexicalError`** | Raised during lexing when a token does not match any pattern or fails a lexical rule (e.g., malformed number, invalid character). |
| **`SyntaxError`** | Raised during parsing when the token stream does not conform to the grammar (e.g., unexpected token, missing semicolon). |
| **`SemanticError`** | Raised during semantic analysis for violations that cannot be detected by the grammar (e.g., undeclared variable, type mismatch, duplicate definition). |
| **`RuntimeError`** | Raised during evaluation or execution of the AST (e.g., division by zero, invalid operation, out‑of‑bounds access). Unlike the other errors, it includes a stack trace to help debug the execution context. |

All of these classes inherit directly from `Error` and simply forward their arguments to the base class constructor, providing a consistent interface.

> ### Runtime Errors and Stack Traces

`RuntimeError` adds a `stack_trace` property, which is a list of strings representing the call stack at the point where the error occurred. This is particularly useful for debugging interpreted languages, as it allows you to trace back through nested function calls or expression evaluations. The stack trace is maintained by the `Context` (via `push_trace` and `pop_trace`) and can be passed to the error when it is raised.

## `ErrorAST`

`ErrorAST` is a specialized subclass of `AST` that represents a node inserted into the syntax tree **exclusively during syntactic analysis** to report **semantic errors** (e.g., type mismatches or other contextual checks performed by reducers). It is **not** intended for syntactic errors (unexpected tokens, malformed productions, etc.); those are handled by the parser's error recovery mechanism without producing `ErrorAST` nodes.

By embedding `ErrorAST` nodes directly into the tree, the parser can continue processing and report multiple semantic errors in a single pass, and later stages can easily detect and handle problematic regions of the AST.

> **NOTE**
`ErrorAST` inherits all attributes of `AST`. Its `is_error` property is always `True`, and the `_errors` internal set stores the reported semantic errors. This allows downstream visitors to easily identify error nodes and skip or handle them appropriately.

**Python:**

```python
from pylgen.common.types import ErrorAST, Symbol, SemanticError

error = SemanticError("semantic error detected", 10, 5, 10, 6)
err_node = ErrorAST(Symbol('error'), 10, 5, 10, 6, {error})
```

**Cython:**

```cython
from pylgen.common.types cimport ErrorAST, Symbol, SemanticError

cdef SemanticError error = SemanticError("semantic error detected", 10, 5, 10, 6)
cdef ErrorAST err_node = ErrorAST(Symbol('error'), 10, 5, 10, 6, {error})
```

## `Token`

`Token` inherits from `AST` and represents a concrete **lexical token**: a specific piece of text identified by the lexer. In addition to its location and symbol (mapped from the token type), it stores the original text and its type. The constructor requires the token text, its **type (must be an instance of a subclass of `TokenType`)**, the corresponding `Symbol`, and the location. It raises a `ValueError` if `type_` is not an instance of a `TokenType` subclass.

**Python:**

```python
from pylgen.common.types import Token,Symbol
from your_tokens import TokenTypeEnum   # your enumeration

symbol = Symbol

token = Token("123", TokenTypeEnum.INTEGER, int_symbol, 1, 5)
```

**Cython:**

```cython
from pylgen.common.types cimport Token
from your_tokens import TokenTypeEnum   # your enumeration

cdef Token token = Token("123", TokenTypeEnum.INTEGER, int_symbol, 1, 5)
```

> **NOTE**
 - Since a `Token` is a leaf node, its `children()` method returns an empty list. This is consistent with the fact that tokens do not have sub‑ASTs.

 - Like all `AST` nodes, `Token` has an `is_error` property; for tokens it is always `False` because they represent valid lexical input.

> ### Additional Attributes

| **Attribute** | **Type** | **Description** |
| :---: | :---: | :---: |
| `text` | `str` | The exact text that matched the pattern (e.g., `"123"`, `"+"`) |
| `type` | subclass of `TokenType` | The token type |

## `ASTListView`

When the parser reduces a production, it passes an `ASTListView` object to the reducer function. This object contains the ASTs of the right-hand side symbols, in the exact order they appear in the production. This view is **inmutable and efficient**: it does not copy the underlying list, but rather provides indexed access and length via optimized internal methods. Indexing is 0‑based, and out‑of‑range access raises `IndexError`.

> ### Methods

| **Method/Operator** | **Description** |
| :---: | :---: |
| **`__getitem__(idx)`** | Gets the AST at position `idx` (0-based). |
| **`__len__()`** | Returns the number of elements |
| **`_get(idx)` (Cython only)** | Same as `__getitem__(idx)`, but a `cdef inline` method for maximum performance. |
| **`_size()` (Cython only)** | Same as `__len__()`, but `cdef inline`. |

> ### Typical Usage

**Python:**

```python
# E -> E + T | T reductor
def e_reductor(asts:ASTListView) -> AST:
    if len(asts) == 1:
        return asts[0]
    left = asts[0]
    right = asts[2]
    op = asts[1]
    return BinaryOpAST(left,right,op.symbol)
```

**Cython:**

```cython
# E -> E + T | T reductor
cdef AST e_reductor(ASTListView asts):
    cdef AST left,right,op
    if asts._size() == 1:
        return asts._get(0)
    left = asts._get(0)
    right = asts._get(2)
    op = asts._get(1)
    return BinaryOpAST(left,right,op._symbol)
```

> **TIP: Pro Tip**
In Cython, prefer `_get(idx)` and `_size()` over `__getitem__(idx)` and `__len__()` to avoid the overhead of type checking and conversion to Python that occurs in the dunder methods. This is especially critical in parsing loops over millions of lines.

## `Table`

`Table` is a specialized container that acts like a dictionary with two-element keys `(str,str)` and `str` values. It is used internally in the `automaton` module to store transitions for automata.

> ### Attributes and Methods

| **Method/Property** | **Description** |
| :---: | :---: |
| **`entries` (property)** | List of all keys `(row,column)`. |
| **`values` (property)** | List of all stored values. |
| **`items` (property)** | List of tuples `(row,column,value)`. |
| **`to_dict()`** | Converts the table to a dictionary `{(row,column): value }`. |
| **`from_dict(data)`** | Loads the data from a dictionary. |
| **`__getitem__((row,column))`** | Gets the value. |
| **`__setitem__((row,column),value)`** | Inserts or updates an entry. |
| **`__delitem__((row,column))`** | Deletes an entry. |

> ### Typical Usage

```python
from pylgen.common import Table

table = Table()
table['q0','a'] = 'q1'
table['q1','b'] = 'q2'

print(table['q0','a'])      # 'q1'
print(table.items)        # [('q0','a','q1'),('q1','b','q2')]
```

> **NOTE: In Cython**
The Cython implementation is virtually identical, but operations are faster because `__getitem__`,`__setitem__`, and `__delitem__` are optimized and avoid type-checking overhead on each access (though they still perform checks in error cases).

## `TokenType`

`TokenType` is a class tha inherits from `StrEnum` (available in Python 3.11+). Its purpose is to provide a type-safe way to define all possible token types your lexer can generate. You must create a subclass with the names you need:

```python
from pylgen.common.enums import TokenType

class MyTokenType(TokenType):
    INTEGER = 'INTEGER'
    FLOAT = 'FLOAT'
    IDENTIFIER = 'IDENTIFIER'
    PLUS = 'PLUS'
    # ...
```

Later, when configuring your lexer, you will use this enumeration to associate each regex pattern with a token type.

> **IMPORTANT: The automatic member `INVALID_TOKEN`**
The base class `TokenType`, through its custom metaclass `TokenTypeMeta`, automatically injects an `INVALID_TOKEN` member into each subclass. This member is used internally to represent invalid tokens.

## Best Practices for Maximum Performance

 - `1`. **Predefine symbols and tables** outside of loops (at the module level) to avoid repeated object creation.
 - `2`. **Use `cdef` for all attributes** of your AST and visitor classes. This turns attribute access into C struct member access, eliminating dictionary lookups.
 - `3`. **In reducers, use `_get(idx)` and `_size()` instead of `__getitem__(idx)` and `__len__()`** when writing Cython code.
 - `4`. **Leverage Cython compilation**: your code can run at speeds very close to C if you follow these guidelines, especially in the critical parsing and evaluation paths.



<!-- source: docs/user-guide/user-guide-lexer.md -->

# The `lexer` Module

The PyLGEN `lexer` module brings together the tools needed for lexical analysis. Its main class, `Lexer`, converts regex patterns into a `DFA` that traverses the input text and produces tokens. `IndentedLexer` extends this functionality to indentation-sensitive languages ​​by generating `INDENT` and `DEDENT` tokens. Additionally, `LexicalRule` allows for the application of further validations to the tokens. Collectively, the module manages priorities, lexical errors, the end-of-file token, and the mapping of tokens to symbols.

## `Lexer`

`Lexer` is the general-purpose class. It converts regex patterns into a DFA that traverses the input linearly.

> ### Example

**Python:**

```python
from pylgen.lexer import Lexer
from pylgen.common.types import Symbol

def to_symbol(token_type:MyTokenType, text:str):
    if token_type == MyTokenType.NUMBER: return number
    return Symbol(text, True)

lexer = Lexer(to_symbol, ignore_pattern=r"\s+")
lexer.set_eof_token("$", MyTokenType.EOF)

lexer[0, MyTokenType.NUMBER] = r"\d+(\.\d+)?"
lexer[1, MyTokenType.OPERATOR] = r"\+|\-|\*|/"
lexer[2, MyTokenType.LPAREN] = r"\("
lexer[3, MyTokenType.RPAREN] = r"\)"
```

**Cython:**

```cython
from pylgen.lexer cimport Lexer
from pylgen.common.types cimport Symbol

cdef Symbol to_symbol(object token_type,str text):
    if token_type == MyTokenType.NUMBER:
        return number
    return Symbol(text,True)

cdef Lexer lexer = Lexer(to_symbol,r'\s+')
lexer._enum_type = MyTokenType
lexer.set_eof_token('$',MyTokenType.EOF)

lexer.add_token_regex(0,MyTokenType.NUMBER,r"\d+(\.\d+)?")
lexer.add_token_regex(1,MyTokenType.OPERATOR,r"\+|\-|\*|/")
lexer.add_token_regex(2,MyTokenType.LPAREN, r"\(")
lexer.add_token_regex(3,MyTokenType.RPAREN, r"\)")
```

> ### Priorities

The first element of the index is the **priority**: lower numbers are attempted first. If two patterns match with the same length, the one with the lower priority value wins. This is the mechanism used to resolve `keyword` vs. `identifier` conflicts: keywords come first.

> ### The mapping function

It receives `(MyTokenType, str)` and returns a `Symbol`. PyLGEN validates its type annotations: the first argument must be a subclass of `TokenType`, the second a `str`, and the return type is a `Symbol`. If the annotations are missing, the lexer fails to initialize.

> ### Attributes and Methods

| **Attribute/Method** | **Type** | **Description** |
| :--- | :--- | :--- |
| `tokens` | generator | Iterates over the tokens of the loaded text. |
| `errors` | `Set[LexicalError]` | Accumulated lexical errors. |
| **`dfa`** | `DFA` | The combined, minimized DFA used for tokenization. Raises `LexerNotInitializedException` if not yet initialized. |
| **`tokens`** | `Iterable[Token]` | A generator that yields tokens from the loaded text. It automatically initializes the lexer and handles ignoring patterns. |
| `load_text(text)` | `None` | Loads text and resets counters. |
| `initialize()` | `None` | Builds the combined DFA. Called automatically. |
| `clear_errors()` | `None` | Clears accumulated errors. |
| `set_eof_token(symbol, type)` | `None` | Defines the end-of-file token. |
| `add_rule(type, rule)` | `None` | Adds a `LexicalRule`. |
| `add_token_regex(self, priority:int,type_: Any, re:str)` | `None` | Adds a token definition |
| **`__setitem__(key:Tuple[int,object], re:str)`** | `None` |Allows adding token patterns with `lexer[priority, type_] = r'regex'` syntax. |

## `IdentedLexer`

`IdentedLexer` extends `Lexer` for indentation-sensitive languages. It generates `INDENT` and `DEDENT` tokens by comparing indentation levels between lines.

> ### Example

**Python:**

```python
from pylgen.lexer import IdentedLexer

lexer = IdentedLexer(to_symbol, ignore_pattern="#[^\n]*\n?")
lexer.set_eof_token("$", MyTokenType.EOF)
lexer.set_ident(MyTokenType.INDENTATION)
lexer.set_indent_symbol(indent_sym)
lexer.set_dedent_symbol(dedent_sym)
lexer.set_text_sanitize_function(sanitize_function)

# adds tokens
```

**Cython:**

```cython
from pylgen.lexer cimport IdentedLexer

cdef IdentedLexer lexer = IdentedLexer(to_symbol, ignore_pattern="#[^\n]*\n?")
lexer._enum_type = MyTokenType
lexer.set_eof_token("$", MyTokenType.EOF)
lexer.set_ident(MyTokenType.INDENTATION)
lexer.set_indent_symbol(indent_sym)
lexer.set_dedent_symbol(dedent_sym)
lexer.set_text_sanitize_function(sanitize_function)

```

> ### Methods

| **Method** | **Description** |
| :--- | :--- |
| `set_ident(type)` | Token type that counts as indentation. |
| `set_indent_symbol(sym)` | `INDENT` symbol. |
| `set_dedent_symbol(sym)` | `DEDENT` symbol. |
| `set_text_sanitize_function(fn)` | Transforms text before tokenization. |

`set_text_sanitize_function` is useful for converting tabs to spaces or replacing empty lines with a marker that the lexer ignores. In indentation-sensitive languages, an empty line containing accidental spaces can confuse level calculations.

## Lexical Rules

A `LexicalRule` validates tokens beyond what a regex can express: numeric ranges, identifiers that do not start with a digit, etc.

> ### Example

**Python:**

```python
from pylgen.analysis.lexical import LexicalRule

class NoLeadingZero(LexicalRule):
    def __init__(self):
        super().__init__("the number cannot start with zero")

        def _check(self, text: str) -> bool:
            return len(text) == 1 or text[0] != "0"

lexer.add_rule(MyTokenType.NUMBER, NoLeadingZero())
```

**Cython:**

```cython
from pylgen.analysis.lexical cimport LexicalRule

cdef class NoLeadingZero(LexicalRule):
    def __init__(self):
        super().__init__("the number cannot start with zero")

        cpdef bool _check(self, str text):
            return len(text) == 1 or text[0] != "0"

lexer.add_rule(MyTokenType.NUMBER, NoLeadingZero())
```

If a rule returns `False`, a `LexicalError` is added to `lexer.errors`. Tokenization continues: you can accumulate multiple errors before stopping.



<!-- source: docs/user-guide/user-guide-grammar.md -->

# The `grammar` Module

The `grammar` module provides the basic tools for defining grammars in PyLGEN: productions, sets of productions, and grammars; both context-free and attributed. Details regarding each class, its attributes, and its methods are explained in the following sections.

> **NOTE: New to grammars?**
If you are unsure about what a non-terminal, a terminal, or a production is, start with [Key Concepts](../getting-started/key-concepts.md) or [Formal Grammars](../formal-foundations/formal-foundations-context-free-grammars.md).

## `Production`

A `Production` is a rule $A \rightarrow \alpha$.

> ### Attributes and Properties

| **Property** | **Type** | **Description** |
| :---: | :---: | :---: |
| **`id`** | `str` | A human‑readable string representation (e.g., `E -> E + T`). |
| **`head`** | `Symbol` | The left‑hand side non‑terminal. |
| **`production`** | `List[Symbol]` | The right‑hand side sequence (list of symbols). |

> ### Typical Usage

**Python:**

```python
from pylgen.common.types import Symbol
from pylgen.grammar.grammar import Production

E = Symbol('E')
T = Symbol('T')
plus = Symbol('+', is_terminal=True)

# Production: E -> E + T
p = Production(E, [E, plus, T])
print(p.id)   # "E -> E + T"
```

**Cython:**

```cython
from pylgen.common.types cimport Symbol
from pylgen.grammar.grammar cimport Production

cdef Symbol E = Symbol('E')
cdef Symbol T = Symbol('T')
cdef Symbol plus = Symbol('+', is_terminal=True)

# Production: E -> E + T
cdef Production p = Production(E, [E, plus, T])
print(p.id)   # "E -> E + T"
```

> **WARNING**
The `head` symbol in the production must be a **non‑terminal**; a `ValueError` is thrown if you attempt to use a terminal.

```python
p = Production(plus,[E,T]) # ValueError is thrown
```

> **IMPORTANT: `Production`'s equality**
Two `Production` objects are equal if they have the same `head` and the same production list (order matters).

## `ProductionsSet`

`ProductionsSet` is a mutable container that holds all productions for a given non‑terminal `head`. It is used internally by `Grammar` to manage the productions of each symbol. It provides a convenient `+=` operator to add a new production.

> ### Methods

| **Method/Operator** | **Description** |
| :---: | :---: |
| **`productions` (property)** | Returns a copy of all production lists as `List[List[Symbol]]`. |
| **`__iadd__`** | Adds a production given as a tuple of `Symbol`; returns self for chaining. |

> ### Usage

```python
from pylgen.grammar.grammar import ProductionsSet
from pylgen.common.types import Symbol

E = Symbol('E')
T = Symbol('T')
plus = Symbol('+', True)

ps = ProductionsSet()
ps += E, plus, T   # adds E -> E + T
ps += T,           # adds E -> T

print(ps.productions)  # [[E, plus, T], [T]]
```

## `AttributedProductionsSet`

`AttributedProductionsSet` extends `ProductionsSet` by allowing each production to carry an associated *reductor*, a callable that transforms the right‑hand side ASTs into a new AST node for the head. This is the cornerstone of attributed grammars.

> **NOTE: The origin of the term "reductor" (or "reducer")**
It stems from the `REDUCE` action of an LR parser. In LR parsing, upon recognizing a production, the parser performs a reduction: it replaces a sequence of symbols with a non-terminal and triggers the associated semantic action. In PyLGEN, the semantic value of each symbol is an AST; thus, this action takes the ASTs of the symbols on the right-hand side of the production and returns the AST corresponding to the non-terminal that replaces those symbols. This function is the "reductor": it reduces a list of child ASTs into a single parent AST. The parser invokes it during a `REDUCE` action (the corresponding syntactic operation); the reducer constitutes the semantic reduction action. Hence the name: it collapses the right-hand side ASTs into a single AST for the left-hand side non-terminal.

> ### Methods

 - **`__iadd__`**: expects a tuple of `(production_tuple, reductor)`, where `production_tuple` is a tuple of `Symbol` and `reductor` is a callable with signature `(ASTListView) -> AST`. The reductor's signature is validated at addition time (must be annotated with [`ASTListView`](../user-guide-common#astlistview) and return [`AST`](../user-guide-common#ast)).

> ### Usage

```python
from pylgen.grammar.grammar import AttributedProductionsSet
from pylgen.common.types import Symbol, ASTListView, AST

class MyAddAST(AST):
    # ...

def make_add(asts: ASTListView) -> AST:
    return MyAddAST(asts[0], asts[2])

E = Symbol('E')
T = Symbol('T')
plus = Symbol('+', True)

aps = AttributedProductionsSet()
aps += (E, plus, T), make_add
```

## `Grammar`

`Grammar` is the central class for defining a context‑free grammar. It manages symbols, productions, and computes `FIRST` and `FOLLOW` sets lazily. It also provides utilities for converting the grammar to a dictionary representation.

> ### Constructor

```python
Grammar(start_symbol: Symbol, end_symbol: str = '\x00')
```

 - `start_symbol`: the initial non‑terminal of the grammar.

 - `end_symbol`: a terminal symbol used as end‑of‑file marker (default `'\x00'`). It is automatically added as a terminal.

> ### Attributes

| **Property** | **Type** | **Description** |
| :---: | :---: | :---: |
| **`id`** | `str` | Unique grammar identifier |
| **`productions`** | `Set[Production]` | All productions in the grammar. |
| **`terminals`** |	`Set[Symbol]` | Set of terminal symbols. |
| **`non_terminals`** |	`Set[Symbol]` | Set of non‑terminal symbols. |
| **`symbols`** | `Set[Symbol]` | All symbols (terminals + non‑terminals). |
| **`start_symbol`** | `Symbol` | The start symbol. |
| **`end_symbol`** | `Symbol` |	The end‑of‑file symbol. |

> ### Methods

| **Method** | **Return Type** | **Description** |
| :---: | :---: | :---: |
| **`first(production: List[Symbol])`** | **`Set[Symbol]`** | returns the `FIRST` set of a sequence of symbols. |
| **`follow(symbol: Symbol)`** | **`Set[Symbol]`** | returns the `FOLLOW` set of a symbol |
| **`to_dict()`** | **`dict`** | returns a dictionary representation of the grammar, listing terminals, non‑terminals, productions, and the epsilon symbol (if any). Useful for debugging or serialization. |

> **WARNING**
A `SymbolNotPresentInGrammarException` is raised if any symbol in the input is not part of the grammar.

> ### Static Utilities

| **Method** | **Description** |
| :---: | :---: |
| **`IsLeftRegular(g: Grammar) -> bool`** | Checks if the grammar is left‑regular. |
| **`IsRightRegular(g: Grammar) -> bool`** | Checks if the grammar is right‑regular. |
| **`IsRegular(g: Grammar) -> bool`** | Checks if the grammar is either left‑ or right‑regular. |
| **`AugmentGrammar(g: Grammar) -> Grammar`** | Creates a new grammar with a new start symbol `S'` and adds production `S' -> S`. |
| **`Reverse(g: Grammar) -> Grammar`** | Reverses the production bodies of every rule, yielding a grammar that recognizes the reversed language. |

> ### Typical Usage

**Python:**

```python
from pylgen.grammar.grammar import Grammar
from pylgen.common.types import Symbol

# symbols definitions ...

G = Grammar(E)

G[E] += E, plus, T
G[E] += T,
```

**Cython:**

```cython
from pylgen.grammar.grammar cimport Grammar
from pylgen.common.types cimport Symbol

# symbols definitions ...

cdef Grammar G = Grammar(E)

G._add_production(E,[E,plus,T])
G._add_production(E,[T])
```

> **WARNING**
Only one `epsilon` symbol can exist per grammar; the code throws a `ValueError` if you try to add another one.

## `AttributedGrammar`

`AttributedGrammar` extends `Grammar` by storing a reductor for each production. It overrides `__getitem__` and `__setitem__` to work with `AttributedProductionsSet`, ensuring that every production added carries a reductor.

> ### Methods

 - `get_reductor(production: Production) -> Callable[[ASTListView], AST]`: returns the reductor associated with the given production.

> ### Typical Usage

**Python:**

```python
from pylgen.grammar.grammar import AttributedGrammar
from pylgen.common.types import Symbol, ASTListView, AST

class MyAddAST(AST):
    # ...

E = Symbol('E')
T = Symbol('T')
plus = Symbol('+', True)

def add_reductor(asts: ASTListView) -> AST:
    # build AST for addition
    return MyAddAST(asts[0], asts[2])

def single_reductor(asts: ASTListView) -> AST:
    return asts[0]

G = AttributedGrammar(E)
G[E] += (E, plus, T), add_reductor
G[E] += (T,), single_reductor   # single reductor
```

**Cython:**

```cython
from pylgen.grammar.grammar cimport AttributedGrammar
from pylgen.common.types cimport Symbol, ASTListView, AST

cdef class MyAddAST(AST):
    # ...

cdef Symbol E = Symbol('E')
cdef Symbol T = Symbol('T')
cdef Symbol plus = Symbol('+', True)

cdef AST add_reductor(ASTListView asts):
    # build AST for addition
    return MyAddAST(asts._get(0), asts._get(2))

cdef AST single_reductor(ASTListView asts):
    return asts._get(0)

G = AttributedGrammar(E)
G._add_attributed_production(E,[E, plus, T], add_reductor)
G._add_attributed_production(E, [T], single_reductor)   # single reductor
```

> **WARNING**
In pure python, the reducer's signature is verified at addition time and must comply with the annotation `(ASTListView) -> AST`.

The parser builder uses the reductors stored in the attributed grammar to construct the AST during parsing.

## Complete Example: Defining an Arithmetic Expression Grammar

Here is a minimal complete example that defines a simple arithmetic grammar with attributed productions (similar to the [Quick Start: Step 6 example](../getting-started/quick-start.md#step-6-attributed-grammar)).

**Python:**

```python
from pylgen.common.types import Symbol, ASTListView, AST
from pylgen.grammar.grammar import AttributedGrammar

# classes definitions
# ...

# Symbols
E = Symbol('E')
T = Symbol('T')
F = Symbol('F')
plus = Symbol('+', True)
mul = Symbol('*', True)
number = Symbol('number', True)
lp = Symbol('(', True)
rp = Symbol(')', True)

# Reductors (simplified)
def binary(asts: ASTListView) -> AST:
    return MyBinaryAST(asts[0], asts[2], asts[1])

def single(asts: ASTListView) -> AST:
    return asts[0]

def paren(asts: ASTListView) -> AST:
    return asts[1]

# Build attributed grammar
G = AttributedGrammar(E, end_symbol='$')
G[E] += (E, plus, T), binary
G[E] += (T,), single
G[T] += (T, mul, F), binary
G[T] += (F,), single
G[F] += (lp, E, rp), paren
G[F] += (number,), single
```

**Cython:**

```cython
from pylgen.common.types cimport Symbol, ASTListView, AST
from pylgen.grammar.grammar cimport AttributedGrammar

# classes definitions
# ...

# Symbols
cdef Symbol E = Symbol('E')
cdef Symbol T = Symbol('T')
cdef Symbol F = Symbol('F')
cdef Symbol plus = Symbol('+', True)
cdef Symbol mul = Symbol('*', True)
cdef Symbol number = Symbol('number', True)
cdef Symbol lp = Symbol('(', True)
cdef Symbol rp = Symbol(')', True)

# Reductors (simplified)
cdef AST binary(ASTListView asts):
    return MyBinaryAST(asts._get(0), asts._get(2), asts._get(1))

cdef AST single(ASTListView asts):
    return asts._get(0)

cdef AST paren(ASTListView asts):
    return asts._get(1)

# Build attributed grammar
cdef AttributedGrammar G = AttributedGrammar(E, end_symbol='$')
G._add_attributed_production(E,[E, plus, T], binary)
G._add_attributed_production(E,[T], single)
G._add_attributed_production(T,[T, mul, F], binary)
G._add_attributed_production(T,[F], single)
G._add_attributed_production(F,[lp, E, rp], paren)
G._add_attributed_production(F,[number], single)
```

This grammar correctly handles precedence (multiplication before addition) and parentheses.



<!-- source: docs/user-guide/user-guide-parser.md -->

# The `parser` Module

The pylgen `parser` module enables the construction of parsers from attributed grammars. Users can choose from various parser types (such as `SLR`, `LR1`, or `LALR1`), with `LALR1` being the default recommendation. Construction is typically performed using `ParserBuilder.build_parser_from_attributed`.

Once created, the parser processes tokens generated by the lexer, returning an Abstract Syntax Tree (`AST`) and accumulating errors in `parser.errors`. It also supports custom reducers, optional parse tree construction, and syntax error recovery via ***panic-mode***. Overall, it serves as a tool for transforming grammars into functional parsers and detecting both syntactic and semantic errors.

## Building a parser

The standard approach is `ParserBuilder.build_parser_from_attributed`:

**Python:**

```python
from pylgen.parser import ParserBuilder, ParserType

parser = ParserBuilder.build_parser_from_attributed(G, ParserType.LALR1)
```

**Cython:**

```cython
from pylgen.parser.parser_builder cimport _build_lalr_parser_from_attribute

cdef BottomUpParser parser = _build_lalr_parser_from_attribute(G)
```

| **Type** | **When to use it** |
| :---: | :---: |
| `SLR` | Simple grammars. Fewer states, less powerful. |
| `LR1` | Grammars that SLR cannot handle. More states, higher memory usage. |
| `LALR1` | Recommended default. Balance between power and size. |

If the grammar contains conflicts, the builder raises a specific exception (`LALRShiftReduceConflictException`, `LALRReduceReduceConflictException`, etc.) containing information about the state and the symbols involved. To inspect a grammar before building the parser, use `lr_inspect_grammar` from `pylgen.visual`.

## Typical Usage

```python
lexer.load_text(source)
ast = parser.parse(lexer.tokens)

if parser.errors:
    for error in parser.errors:
        print(error)
else:
    print("Parse OK")
```

> **NOTE**
`parse` **does not raise exceptions** for syntax errors. It accumulates them in `parser.errors` and continues parsing whenever possible. This allows for the detection of multiple errors in a single pass.

## Parser's Attributes and Methods

| **Member** | **Type** | **Description** |
| :--- | :--- | :--- |
| `parse(tokens)` | `AST` | Returns the root of the tree. |
| `errors` | `List[Error]` | Accumulated errors. |
| `syntax_errors` | `bool` | Returns `True` if any syntax error ocurred |
| `reset()` | `None` | Clears state and errors. |
| `set_draw_parse_tree_flag(flag)` | `None` | Enables parse tree construction. |
| `parse_tree` | `ParseTreeNode` | Root of the parse tree (if enabled). |

## Reducers and the parser

Every production in the attributed grammar must have a corresponding reducer. **There is no default reducer.** If a reduction is triggered for a production without a reducer, the parser fails.

**Python:**

```python

# ASTs definitions

def number_reductor(asts:ASTListView) -> AST:
    return MyAST()

G[Number] += (number,), number_reductor
```

**Cython:**

```cython

# ASTs definitions

cdef AST number_reductor(ASTListView asts):
    return MyAST()

G._add_attributed_production(Number,[number],number_reductor)
```

If you want a generic reducer for all uncovered productions, assign it explicitly. It is your choice, not something the parser does for you.

## Parse Tree vs. AST

The parser builds an **AST** by default. If you also want the **parse tree** (the complete derivation including all terminals and non-terminals), enable it before parsing:

```python
parser.set_draw_parse_tree_flag(True)
ast = parser.parse(lexer.tokens)
tree = parser.parse_tree
```

The parse tree is useful for debugging grammars and for visualization. It does not replace the AST; they are two distinct trees. The AST is constructed by the reducers, whereas the parse tree is built by the parser itself.

## Syntax errors

When the parser cannot proceed, it applies **panic-mode recovery**: it discards tokens until it finds one that allows it to continue. The accumulated errors include the exact position of the problematic token.

```python
for error in parser.errors:
    print(error)   # SYNTAX ERROR at line 1: Unexpected symbol ")"
```

> **IMPORTANT**
If any `ErrorAST` node was added, the corresponding semantic errors will also be in `parser.errors`; it is recommended to check `parser.syntax_errors` to determine whether to proceed with the semantic analysis step, rather than simply checking if errors were detected.

To report them with context in an editor, use `error.start_position` and `error.end_position`. Each error knows which snippet of code caused it.



<!-- source: docs/user-guide/user-guide-analysis.md -->

# The `analysis` Module

The `analysis` module provides the infrastructure for AST processing, semantic checks, and evaluation. It is built on the **Visitor** and **Strategy** patterns.

## `Context`

The `Context` class is the central state repository. Subclass it to add language-specific data (symbol tables, type environments, etc.).

> ### Attributes and Methods

| **Attribute**/**Method** | **Type** | **Description** |
| :---: | :---: | :---: |
| `push_trace(trace:str)` | `None` | Adds a trace entry |
| `pop_trace()` | `None` | Removes the top trace |
| `push_new_scope()` | `None` | Pushes a new scope. **Must override** |
| `pop_scope()` | `None` | Pops the current scope. **Must override** |
| `add_semantic_error(error:SemanticError)` | `None` | Adds a semantic error |
| `add_runtime_error(ast:AST, error:RuntimeError)` | `None` | Adds a runtime error. **Must override** |
| `clear_runtime_errors()` | `None` | Clears all runtime errors. **Must override** |
| `clear_semantic_errors()` | `None` | Clears all semantic errors |
| `clear_errors()` | `None` | Clears all errors and stack trace. |
| `get_runtime_errors()` | `List[RuntimeError]` | Gets all runtime errors. **Must override** |
| `reset()`	| `None` | Resets the context |
| `errors` | `List[SemanticError | RuntimeError]` | All semantic and runtime errors |
| `stack_trace` | `List[str]` | Current stack trace |

> **WARNING**
All methods that must be overridden raise a `NotImplementedError` if called without being overridden.

## Visitor Framework

The framework consists of four collaborating components.

| **Component** | **Key Methods** |
| :---: | :---: |
| **`ASTVisitor`** | `visit(ast:AST, context:Context)`, `_check_context_type(context:Context)` |
| **`ASTChildrenSelector`** | `select_children(ast:AST, context:Context) -> List[AST]` |
| **`TraversalStrategy`** | `init(root:AST)`, `has_next() -> bool`, `current(context:Context) -> AST`, `reset()`,<br> `add_selector(ast_type:type, selector:ASTChildrenSelector)`, `set_default_selector(selector:ASTChildrenSelector)` |
| **`ASTWalker`** | `add_visitor(ast_type:type, visitor:ASTVisitor)`, `set_default_visitor(visitor:ASTVisitor)`, `walk(ast:AST)` |

> **IMPORTANT**
`add_selector`, `set_default_selector`, `add_visitor`, and `set_default_visitor` use `inspect` to verify that the context type annotation matches the expected type.

> ### Typical Usage

```python
context = MyContext()
strategy = MyStrategy()
strategy.add_selector(MyNode,MyNodeSelector())
strategy.set_default_selector(DefaultSelector())
walker = ASTWalker(context, strategy)
walker.add_visitor(MyNode, MyVisitor())
walker.set_default_visitor(DefaultVisitor())
walker.walk(ast)

if context.errors:
    for error in context.errors:
        print(error)
else:
    print("Analysis OK")
```

> **NOTE**
The walker applies visitors in the order determined by the traversal strategy. Selectors decide which children are visited.

> **TIP: Best Practices**
- Always call `_check_context_type` at the start of visit and `select_children`.

- Keep visitors focused on a single responsibility.

- Use the default visitor for fallback behavior.

- Clear the context between independent compilations with `context.reset()`.



<!-- source: docs/user-guide/user-guide-regex.md -->

# The `regex` Module

The `regex` module is a standalone regular expression engine. It parses regex strings into an AST, evaluates them into NFAs or DFAs, converts between automata and regular grammars, and synthesizes regexes from automata. It is the foundation of the lexer.

## `RegexEngine`

Static class providing the primary API. All methods are stateless and thread‑safe.

> ### Methods

| **Method** | **Description** |
| :---: | :---: |
| `Parse(re: str) -> DFA` | Parses a regex and returns a minimized DFA |
| `GetAutomaton(g: Grammar) -> DFA` | Converts a regular grammar into a minimized DFA. Raises `ValueError` if `g` is not regular |
| `GetGrammar(automaton: Automaton) -> Grammar` | Converts an automaton into a right‑linear grammar |
| `GetRegex(automaton: Automaton) -> str` | Derives a regex using state elimination |
| `BuildRegexParser() -> Parser` | Returns a LALR(1) parser for regexes |
| `BuildRegexLexer() -> BaseLexer` | Returns a lexer for regex strings |

## Examples

> ### Parsing a Regex into a DFA

**Python:**

```python
from pylgen.regex import RegexEngine

dfa = RegexEngine.Parse('a(b|c)*d')
assert dfa.accept(['a', 'b', 'c', 'd'])
assert dfa.accept(['a', 'd'])
assert dfa.accept(['a', 'b', 'd'])
assert dfa.accept(['a', 'c', 'd'])
assert not dfa.accept(['a', 'b', 'b'])
```

**Cython:**

```cython
from pylgen.regex.engine cimport _parse
from pylgen.automaton.automaton cimport DFA

cdef DFA dfa = _parse('a(b|c)*d')
assert dfa.accept(['a', 'b', 'c', 'd'])
assert dfa.accept(['a', 'd'])
assert dfa.accept(['a', 'b', 'd'])
assert dfa.accept(['a', 'c', 'd'])
assert not dfa.accept(['a', 'b', 'b'])
```

#### Supported Syntax

 - Character classes: `[abc]`, `[^abc]`, `[a-z]`

 - Predefined constants: `\d`, `\D`, `\s`, `\S`, `\w`, `\W`, .

 - Quantifiers: `*`, `+`, `?`, `{min,max}`

 - Grouping: `(regex)`

 - Escapes: `\(`, `\)`, `\[`, `\]`, `\{`, `\}`, `\-`, `\*`, `\+`, `\?`, `\^`, `\|`, `\.`, `\,`.

> **IMPORTANT**
The constants (`\D`, `\S`, `\W`, `.`, and the default negated class) operate over the extended Latin characters alphabet (accented vowels, diaeresis, and eñe: `á é í ó ú ü ñ` and their uppercase forms).

> ### Converting a Regular Grammar to a DFA

**Python:**

```python
from pylgen.common.types import Symbol
from pylgen.grammar.grammar import Grammar
from pylgen.regex import RegexEngine

S = Symbol('S')
a = Symbol('a', True)
b = Symbol('b', True)

G = Grammar(S)
G[S] += (a, S)   # S -> a S
G[S] += (b,)     # S -> b

dfa = RegexEngine.GetAutomaton(G)
```

**Cython:**

```cython
from pylgen.common.types cimport Symbol
from pylgen.grammar.grammar cimport Grammar
from pylgen.regex.engine cimport _get_automaton
from pylgen.automaton.automaton cimport DFA

cdef Symbol S = Symbol('S')
cdef Symbol a = Symbol('a', True)
cdef Symbol b = Symbol('b', True)

cdef Grammar G = Grammar(S)
G._add_production(S, [a, S])   # S -> a S
G._add_production(S, [b])      # S -> b

cdef DFA dfa = _get_automaton(G)
```

> ### Deriving a Regex from an Automaton

**Python:**

```python
from pylgen.automaton.automaton import DFA, State
from pylgen.regex import RegexEngine

dfa = DFA('q0', None, {'a', 'b'}, True)
q0 = dfa.start_state
dfa += q0, 'a', q0
dfa += q0, 'b', q0

regex = RegexEngine.GetRegex(dfa)
print(regex)  # (a|b)*
```

**Cython:**

```cython
from pylgen.automaton.automaton cimport DFA, State
from pylgen.regex.engine cimport _get_regex

cdef DFA dfa = DFA('q0', None, {'a', 'b'}, True)
cdef State q0 = dfa._start_state
dfa.add_transition(q0, q0, 'a')
dfa.add_transition(q0, q0, 'b')

cdef str regex = _get_regex(dfa)
print(regex)  # (a|b)*
```



<!-- source: docs/user-guide/user-guide-automaton.md -->

# The `automaton` Module

The `automaton` module implements finite automata: `DFA`, `NFA`, and automata with ε‑moves. It supports manual construction and automatic generation from words.

## `State`

State is immutable. Its `id`, `value`, and `is_accept` cannot be modified after creation.

> ### Attributes

| **Property** | **Type** | **Default** | **Description** |
| :---: | :---: | :---: | :---: |
| **`id`** | `str` | Required | Unique identifier |
| **`value`** | `Any` | Required | Semantic value associated with the state |
| **`is_accept`** | `bool` | `False` | Whether the state is accepting |

> **IMPORTANT: `State`'s Equality**
The equality of two states is based solely on their ID; 2 states are considered equals if and only if its ids are equals.

> ### Typical Usage

**Python:**

```python
from pylgen.automaton import State

s1 = State('s1', 's1')       # non-accepting
s2 = State('s2', 10, True)   # accepting, value 10

print(s1.id, s1.value, s1.is_accept)
print(s2.id, s2.value, s2.is_accept)
```

**Cython:**

```cython
from pylgen.automaton cimport State

cdef State s1 = State('s1', 's1')
cdef State s2 = State('s2', 10, True)

print(s1._id, s1._value, s1._is_accept)
print(s2._id, s2._value, s2._is_accept)
```

## `Automaton`

`Automaton` is the abstract base class and cannot be instantiated. It provides state management, alphabet, transitions, ε‑transitions, and derived properties.

> ### Attributes

| **Attribute** | **Type** | **Description** |
| :---: | :---: | :---: |
| **`id`** | `str` | Unique identifier computed from the automaton structure |
| **`alphabet`** | `Set[str]` | Copy of the alphabet |
| **`start_state`** | `State` | Copy of the initial state |
| **`current_state`** | `State` | Copy of the current state |
| **`states`** | `Set[State]` | All states |
| **`finals`** | `Set[State]` | Accepting states |
| **`is_complete`** | `bool` | `True` if all transitions are defined |
| **`transition_function`** | `Dict[Tuple[str, str], str]` | Transition table |
| **`epsilon_transitions`** | `Dict[str, Set[str]]` | ε‑transitions |
| **`is_empty`** | `bool` | Whether the accepted language is empty |
| **`is_finite`** | `bool` | Whether the language is finite |

> ### Methods

| **Method** | **Description** |
| :---: | :---: |
| **`add_transition(from_state, to_state, symbol)`** | Adds a deterministic transition |
| **`has_transition(state, symbol) -> bool`** | Checks if a transition exists |
| **`next(state, symbol) -> State`** | Returns the target state |
| **`reset()`** | Resets the current state to the initial state |
| **`closure(state) -> Set[State]`** | Computes the ε‑closure |
| **`make_complete()`** | Adds a sink state and missing transitions |
| **`restore_to_before_complete()`** | Reverts completion |
| **`extend_alphabet(symbols)`** | Extends the alphabet |

> ### Operators

| **Operator** | **Method** | **Return** | **Description** |
| :---: | :---: | :---: | :---: |
| **`|`** | `__or__` | `NFA` | Union |
| **`&`** | `__and__` | `DFA` | Intersection |
| **`+`** | `__add__` | `NFA` | Concatenation |

> ### Static Methods

| **Static** | **Method** | **Return** | **Description** |
| :---: | :---: | :---: | :---: |
| **`Union(automatons)`** | `NFA` | Union with a new start and ε‑transitions |
| **`Complement(automaton)`** | `DFA` | Complement. Determinizes and minimizes if needed |
| **`Intersection(automatons)`** | `DFA` | Cartesian product |
| **`Concat(first, second)`** | `NFA` | Concatenation with ε‑transitions |
| **`KleeneStar(automaton)`** | `NFA` | Kleene star |
| **`PositiveClosure(automaton)`** | `NFA` | Positive closure |
| **`Optional(automaton)`** | `NFA` | Optional |
| **`Reverse(automaton)`** | `NFA` | Reverses the language |

## `DFA`

The `DFA` class inherits from `Automaton` and adds deterministic behavior.

> ### Methods

| **Method** | **Description** |
| :---: | :---: |
| **`walk(symbol)`** | Advances the current state. Enters stuck state on missing transition |
| **`accept(string)`** | Returns `True` if the string is accepted. Resets afterward. |
| **`minimize(initial_partition=[])`** | Applies [**Hopcroft's algorithm**](https://en.wikipedia.org/wiki/DFA_minimization). Completes temporarily if needed |
| **`__iadd__(transition:Tuple[State,str,State])`** | Adds a transition from the tuple `(from_state,symbol,to_state)` with `+=` operator |

#### Typical Usage

**Python:**

```python
from pylgen.automaton import DFA, State

dfa = DFA("q0", "even", {"a", "b"}, True)
q0 = dfa.start_state
q1 = State("q1", "odd")

dfa += q0, 'a', q1
dfa += q1, 'a', q0
dfa += q0, 'b', q0
dfa += q1, 'b', q1

assert dfa.accept(['a', 'b', 'a'])
```

**Cython:**

```cython
from pylgen.automaton cimport DFA, State

cdef DFA dfa = DFA("q0", "even", {"a", "b"}, True)
cdef State q0 = dfa._start_state
cdef State q1 = State("q1", "odd")

dfa.add_transition(q0, q1, 'a')
dfa.add_transition(q1, q0, 'a')
dfa.add_transition(q0, q0, 'b')
dfa.add_transition(q1, q1, 'b')

assert dfa.accept(['a', 'b', 'a'])
```

## `NFA`

The `NFA` class inherits from `DFA` and adds supporting for ε‑transitions and nondeterminism.

> ### Methods

| **Method** | **Description** |
| :---: | :---: |
| **`add_epsilon_transition(from_state, to_state)`** | Adds an ε‑transition |
| **`to_deterministic()`** | Converts to an equivalent `DFA` via subset construction |
| **`__iadd__(transition:Tuple[State,str,State])`** | Adds a normal transition from the tuple `(from_state,symbol,to_state)` with the `+=` operator |

> ### Typical Usage

**Python:**

```python
union = dfa1 | dfa2   # NFA with new start and ε‑transitions
```

**Cython:**

```cython
from pylgen.automaton cimport NFA, _automaton_union

cdef NFA union = _automaton_union({dfa1, dfa2})
```

## Factory Functions

| **Function** | **Return** | **Description** |
| :---: | :---: | :---: |
| **`create_dfa(states, transition_function, start_id, alphabet)`** | `DFA` | Builds a `DFA` from serialized data |
| **`create_nfa(states, transition_function, epsilon_transitions, start_id, alphabet)`** | `NFA` | Builds an `NFA` from serialized data |
| `get_word_automaton(word)` | `DFA` | Builds the `DFA` that recognizes exactly that one word |
| `get_words_automaton(words)` | `NFA` | Builds the `NFA` that recognizes the union of several words |
| `get_word_automaton_with_value(word, value, only_finals=False)` | `DFA` | Assigns a value to states |
| `get_words_automaton_with_value(words, value, only_finals=False)` | `NFA` | Same, for several words |

## Complete Example: Integer Recognizer

**Python:**

```python
from pylgen.automaton import DFA, State

digits = set("0123456789")
alphabet = digits | {"+", "-"}

q0 = State("q0", None)
q1 = State("q1", None)
q2 = State("q2", "integer", is_accept=True)

dfa = DFA("q0", None, alphabet)
dfa += q0, '+', q1
dfa += q0, '-', q1
for d in digits:
    dfa += q0, d, q2
    dfa += q1, d, q2
    dfa += q2, d, q2

dfa.make_complete()

assert dfa.accept(['1', '2', '3'])
assert dfa.accept(['+', '5'])
assert not dfa.accept(['-'])
```

**Cython:**

```cython
from pylgen.automaton cimport DFA, State

cdef set digits = set("0123456789")
cdef set alphabet = digits | {"+", "-"}

cdef State q0 = State("q0", None)
cdef State q1 = State("q1", None)
cdef State q2 = State("q2", "integer", is_accept=True)

cdef DFA dfa = DFA("q0", None, alphabet)
dfa.add_transition(q0, q1, '+')
dfa.add_transition(q0, q1, '-')
for d in digits:
    dfa.add_transition(q0, q2, d)
    dfa.add_transition(q1, q2, d)
    dfa.add_transition(q2, q2, d)

dfa.make_complete()

assert dfa.accept(['1', '2', '3'])
assert dfa.accept(['+', '5'])
assert not dfa.accept(['-'])
```



<!-- source: docs/user-guide/user-guide-visual.md -->

# The `visual` Module

The `visual` module generates interactive HTML visualizations using `networkx` and `pyvis`. It supports **automata**, **lexers**, **ASTs**, **parse trees**, **parsing tables**, and **propagation edges**. Outputs are **self‑contained HTML files** with **optional caching for offline use**.

## Public Functions

| **Function** | **Purpose** |
| :---: | :---: |
| **`draw_automaton`** | Visualize a `DFA` or `NFA` |
| **`draw_lexer`** | Visualize the `DFA` underlying a lexer |
| **`draw_ast`** | Visualize an AST |
| **`draw_parse_tree`** | Visualize a parse tree |
| **`show_propagation_edges_table`** | Show LALR propagation edges |
| **`lr_inspect_grammar`** | Inspect `ACTION`/`GOTO` tables and conflicts |
| **`set_cache_file`** | Set the cache file for external resources |

## Drawing Automata and Lexers

> ### `draw_automaton(automaton, **kwargs)`

Generates an interactive HTML visualization of a finite automaton. Accept states are green, the start state is white with a green border if it is also accepting, and other states are blue. Epsilon transitions appear as dashed edges.

| **Parameter** | **Description** |
| :---: | :---: |
| **`automaton`** | An instance of `pylgen.automaton.Automaton` |
| **`**kwargs`** | Common parameters. Default filename: `automaton-{automaton.id}` |

#### Example

```python
from pylgen.visual import draw_automaton

draw_automaton(my_automaton, show=True, physics=True)
```

> ### draw_lexer(lexer, **kwargs)

Convenience function that extracts the `DFA` from a lexer and calls `draw_automaton` on it.

#### Example

```python
from pylgen.visual import draw_lexer

draw_lexer(my_lexer, filename='lexer_dfa', show=True)
```

## Drawing Abstract Syntax Trees and Parse Trees

> ### `draw_ast(ast, **kwargs)`

Visualizes an `AST` as a hierarchical tree. Each node displays its symbol; a tooltip shows non‑private attributes. The tree is traversed recursively via `children()`.

| **Parameter** | **Description** |
| :---: | :---: |
| **`ast`** | Root AST node, an instance of `pylgen.common.types.AST` |
| **`**kwargs`** | Common parameters. Default filename: `ast` |

#### Example

```python
from pylgen.visual import draw_ast

draw_ast(root, show=True)
```

> ### `draw_parse_tree(tree, **kwargs)`

Visualizes the parse tree (concrete syntax tree) built by the parser. It contains all grammar symbols and is useful for debugging grammar rules.

| **Parameter** | **Description** |
| :---: | :---: |
| **`tree`** | An instance of `pylgen.parser.parser.ParseTreeNode`, normally taken from a parser that already has parsed something correctly with its `_draw_parse_tree` flag setted to `True`, via `parser.parse_tree` attribute | 
| **`**kwargs`** | Common parameters. Default filename: `parse tree` |

#### Example

```python
from pylgen.visual import draw_parse_tree

parser.set_draw_parse_tree_flag(True)
parser.parse(lexer.tokens)
draw_parse_tree(parser.parse_tree, show=True)
```

> **WARNING**
`parser.set_draw_parse_tree_flag(True)` must be called before parsing; otherwise no parse tree is produced.

## Inspecting LR Grammars

> ### `show_propagation_edges_table(g, **kwargs)`

Generates an HTML table of all propagation edges used in LALR lookahead computation. Lists source state/item, trigger symbol, destination state/item, and lookaheads.

| **Parameter** | **Description** |
| :---: | :---: |
| **`g`** | A instance of `pylgen.grammar.grammar.Grammar` |
| **`**kwargs`** | `filename`, `show`, `cache` |

#### Example

```python
from pylgen.visual import show_propagation_edges_table

show_propagation_edges_table(grammar, show=True)
```

> ### `lr_inspect_grammar(g, type_=ParserType.LALR1, **kwargs) -> bool`

Performs full LR analysis and generates an HTML report with `ACTION` and `GOTO` tables. Conflicts are highlighted in red. Returns `True` if conflicts exist.

| **Parameter** | **Description** |
| :---: | :---: |
| **`g`** | The instance of `pylgen.grammar.grammar.Grammar` to inspect |
| **`type_`** | `ParserType.SLR`, `ParserType.LR1`, or `ParserType.LALR1`. Others raise `NotImplementedError` |
| **`**kwargs`** | `filename`, `show`, `cache`, `report`. If `report=False`, no file is written but conflict check still runs |

#### Example

```python
from pylgen.visual import lr_inspect_grammar
from pylgen.parser.parser_type import ParserType

has_conflicts = lr_inspect_grammar(
    grammar, ParserType.LALR1,
    filename='my_grammar_report', show=True, report=True
)
if has_conflicts:
    print("Grammar has conflicts. Check the report for details.")
```

> ### Examples

#### 1: Classic LALR1 Grammar Analysis (No Conflicts)

The following example demonstrates how to visualize the propagation edges and the `ACTION/GOTO` tables for a classic LALR(1) grammar (the well‑known `S -> L = R | R, L -> * R | id, R -> L` grammar). This grammar is LALR(1) and has no conflicts.

```python
from pylgen.common.types import Symbol
from pylgen.grammar import Grammar
from pylgen.visual import show_propagation_edges_table,lr_inspect_grammar,set_cache_file

set_cache_file('cache.pkl')

S = Symbol('S')
L = Symbol('L')
R = Symbol('R')

mul = Symbol('*',True)
id_ = Symbol('id',True)
eq = Symbol('=',True)

G = Grammar(S,'$')

G[S] += L,eq,R
G[S] += R,

G[L] += mul,R
G[L] += id_,

G[R] += L,

show_propagation_edges_table(G,show=True,cache=True,filename='edges_table')
lr_inspect_grammar(G,'LALR1',show=True,report=True,cache=True,filename='inspect')
```

##### Propagation Edges

##### `ACTION` and `GOTO` Tables

#### 2: LALR(1) Problematic Grammar Analysis

This example shows a grammar that contains ambiguities, resulting in shift/reduce and reduce/reduce conflicts. The generated tables highlight the conflicting cells in red.

```python
from pylgen.common.types import Symbol
from pylgen.grammar import Grammar
from pylgen.visual import show_propagation_edges_table,lr_inspect_grammar,set_cache_file

set_cache_file('cache.pkl')

S = Symbol('S')

E = Symbol('E')
A = Symbol('A')
B = Symbol('B')
C = Symbol('C')

mul = Symbol('*',True)
id_ = Symbol('id',True)
plus = Symbol('+',True)

G = Grammar(S,'$')

G[S] += E,
G[S] += A,

G[E] += E,plus,E
G[E] += E,mul,E
G[E] += id_,

G[A] += B,
G[A] += C,

G[B] += id_,
G[C] += id_,

show_propagation_edges_table(G,show=True,cache=True,filename='edges_table_conflict')
lr_inspect_grammar(G,'LALR1',show=True,report=True,cache=True,filename='inspect_conflict')
```

##### Propagation Edges

##### `ACTION` and `GOTO` Tables

## Cache Management

> ### `set_cache_file(filename: str) -> None`

Sets the global cache file path used when `cache=True` in any drawing function. The cache stores downloaded external resources (CSS and JavaScript from CDNs) so that visualizations can be opened offline without repeated network requests. The cache is a Python pickle file that maps filenames to their content.

| **Parameter** | **Description** |
| :---: | :---: |
| **`filename`** | Path to the cache file |

> **WARNING**
Raises `ValueError` if empty or `None`. The cache path applies to future calls. Existing entries are reused; only new resources are downloaded.

#### Example

```python
from pylgen.visual import set_cache_file

set_cache_file('my_cache.pkl')
```

## Common Parameters

> ### Methods x Parameters Table

| **Method** | **`filename`** | **`show`** | **`cache`** | **`physics`** | **`select_menu`** | **`filter_menu`** | **`nodes`** | **`edges`** | **`as_tree`** | **`report`** |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`draw_automaton`** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **`draw_lexer`** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **`draw_ast`** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **`draw_parse_tree_from_parser`** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **`show_propagation_edges_table`** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **`lr_inspect_grammar`** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

> ### Parameters Details

| **Parameter** | **Type** | **Default** | **Description** |
| :---: | :---: | :---: | :---: |
| **`filename`** | `str` | Depends on the function | Name of the output HTML file (without extension). |
| **`show`** | `bool` | `False` | If `True`, opens the generated HTML file in your default browser immediately. |
| **`cache`** | `bool` | `False` | If `True`, uses a global cache file (set via `set_cache_file()`) to store downloaded CSS/JS resources for offline reuse. |
| **`physics`** | `bool` | `False` | If `True`, enables physics controls in the interactive graph. |
| **`select_menu`** | `bool` | `False` | If `True`, shows a selection menu in the visualization. |
| **`filter_menu`** | `bool` | `False` | If `True`, shows a filter menu. |
| **`nodes`** | `bool` | `False` | If `True`, displays node controls. |
| **`edges`** | `bool` | `False` | If `True`, displays edge controls. |
| **`as_tree`** | `bool` | `False` | If `True`, lays out the graph as a hierarchical tree. |
| **`report`** | `bool` | `False` | If `True`, the HTML report is generated; if `False`, no file is written (but the conflict check is still performed). |

> **NOTE**
When `cache=True`, you must have previously called `set_cache_file()` to specify the cache file path. Otherwise, a `ValueError` is raised.

## Best Practices

 - Enable caching for repeated use.

 - Use show=True for quick debugging; otherwise open the HTML files manually.

 - Disable physics for large graphs; enable it interactively if needed.
